---
title: Profiling
layout: template
filename: profiling.md
---

# Profiling your FastAPI application

Every other page in this project answers "how much faster" with `ab` load-test numbers. This page answers "why", and shows the actual investigation — not just the conclusion — using [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile), Python's built-in deterministic profiler. Credit for the cProfile basics goes to this [cProfile walkthrough](https://machinelearningplus.com/python/cprofile-how-to-profile-your-python-code/); this page applies the same tool, step by step, to explain the [BaseHTTPMiddleware vs Starlette ASGI middleware](middleware) result measured elsewhere on this site.

## Why profile instead of just load-testing

`ab` (and similar tools) tell you throughput and latency dropped. They don't tell you *where* the time went — which function, called how many times, at what depth of the call stack. cProfile does. Point it at a piece of code and it counts, for every function called:

* **ncalls** — how many times it was called (`x/y` means `y` primitive calls, `x` total including recursion)
* **tottime** — time spent in the function itself, excluding sub-calls
* **cumtime** — time spent in the function *and* everything it calls
* **percall** — the above divided by ncalls

`tottime` tells you what's actually hot; `cumtime` tells you which call path is expensive. Neither tells you *why* on its own — that takes comparing two profiles and walking the call graph, which is what the rest of this page does.

## Test environment

> CI run [35014905057](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/35014905057) — Python 3.14, Ubuntu latest, `profiling` job.

* Same dependency pins as this CI run: FastAPI 0.139.2, Starlette 1.3.1, httpx 0.28.1
* The profiler is pointed at `app_files/app.py`'s ASGI callable directly, bypassing the HTTP client/server entirely, so it isolates middleware overhead from network and test-tooling overhead
* Script: [`test_files/profile_middleware.py`](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/profile_middleware.py) — reproduce locally with:
```shell
MODE=baseline  PSTATS_OUT=baseline.pstats  python3 test_files/profile_middleware.py
MODE=base_http PSTATS_OUT=base_http.pstats python3 test_files/profile_middleware.py
MODE=starlette PSTATS_OUT=starlette.pstats python3 test_files/profile_middleware.py
```
* The same three runs execute in CI on every push (job `profiling` in [`performance_tuning_measurements.yml`](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/.github/workflows/performance_tuning_measurements.yml)), each uploaded as a `Profiling-<python-version>` artifact containing the raw `.pstats` dumps plus the `print_stats()` text output. Everything below was read out of that artifact — nothing is hand-typed or estimated.

## Profiling the app directly

The simplest way to profile a function or a block of code is `cProfile.run()`:

```python
import cProfile
cProfile.run("20 + 10")
```

For anything beyond a one-liner, the `Profile` class gives more control, and [`pstats`](https://docs.python.org/3/library/profile.html#pstats.Stats) lets you dump, sort, and inspect the results:

```python
import cProfile, pstats

profiler = cProfile.Profile()
profiler.enable()
main()                       # the code you want to measure
profiler.disable()

pstats.Stats(profiler).dump_stats("profile.pstats")
```

Since FastAPI request handling is async, `enable()`/`disable()` must wrap the event loop that drives the ASGI app, not a synchronous call — `test_files/profile_middleware.py` builds a minimal ASGI `scope`/`receive`/`send` triple, calls `app(scope, receive, send)` 2000 times inside one `asyncio.run()`, and profiles that loop. This avoids pulling `TestClient`'s own thread-portal machinery into the profile, which would otherwise dominate `tottime` and hide the actual middleware cost.

Once you have a `.pstats` file, you don't need a script to read it — `python -m pstats <file>` opens an interactive browser with `sort`, `stats`, `callers` and `callees` commands. That browser is what the rest of this page uses.

## The investigation

### Step 1 — keep everything identical except the one variable under test

Before trusting any difference between two profiles, make sure there's only one difference *causing* it. All three runs here use the exact same driver script, the same `N=2000` iterations, the same endpoint (`/sync/items/`) and the same JSON payload. The only thing that changes between `baseline` and `base_http` is one line in `app_files/app.py`:

```python
app.add_middleware(CustomHeaderMiddleware)   # a BaseHTTPMiddleware subclass, see middleware.md
```

Same request count, same code path, one middleware added — whatever the profiler shows moving is caused by that middleware, not by noise.

### Step 2 — open the file and look at the totals first

Before reading a single row, `pstats` prints a one-line summary. That's the cheapest signal there is:

```shell
$ python -m pstats baseline.pstats
Welcome to the profile statistics browser.
baseline.pstats% sort tottime
baseline.pstats% stats 10
Tue Sep 15 21:40:27 2026    baseline.pstats

         1413940 function calls (1379943 primitive calls) in 0.782 seconds
```

```shell
$ python -m pstats base_http.pstats
Welcome to the profile statistics browser.
base_http.pstats% sort tottime
base_http.pstats% stats 10
Tue Sep 15 21:40:27 2026    base_http.pstats

         3434000 function calls (3380000 primitive calls) in 1.950 seconds
```

Same 2000 requests, but **2.4x the function calls** and **2.5x the wall time**. This alone is worth knowing — the middleware isn't a fixed cost that amortizes away, it scales with the request count. But the summary line doesn't say *why*, so it's time to look at the rows underneath it.

### Step 3 — `tottime` says the event loop got busier, not why

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
30001/30000 0.103   0.000    1.878    0.000 base_events.py:1977(_run_once)
54000/52000 0.047   0.000    1.647    0.000 {method 'run' of '_contextvars.Context' objects}
   10000    0.043    0.000    0.776    0.000 routing.py:399(app)
   30000    0.040    0.000    0.040    0.000 {method 'poll' of 'select.epoll' objects}
20000/2000 0.039    0.000    0.076    0.000 encoders.py:129(jsonable_encoder)
```

Compare to baseline's top rows, where `select.epoll` polled **8000** times (not 30000) and there's no `_contextvars.Context.run` anywhere near the top. Something is waking the event loop 3.75x more often per request. But `_run_once`, `Context.run` and `select.epoll` are generic asyncio machinery — they don't say *what* is running inside them. `tottime` found the smoking gun's noise, not the gun. Time to switch to `cumtime`, which shows call chains instead of isolated frames.

### Step 4 — `cumulative` shows two frames that don't exist in the baseline

```shell
base_http.pstats% sort cumulative
base_http.pstats% stats 15
```

```
  ncalls  tottime  percall  cumtime  percall filename:lineno(function)
30001/30000 0.103   0.000    1.878    0.000 base_events.py:1977(_run_once)
   50000    0.026    0.000    1.671    0.000 events.py:92(_run)
54000/52000 0.047   0.000    1.647    0.000 {method 'run' of '_contextvars.Context' objects}
   20000    0.015    0.000    1.062    0.000 _tasks.py:322(_run_coro)
   16000    0.007    0.000    1.009    0.000 base.py:139(coro)
   16000    0.009    0.000    0.998    0.000 exceptions.py:47(__call__)
32000/16000 0.011   0.000    0.985    0.000 _exception_handler.py:31(wrapped_app)
   16000    0.009    0.000    0.980    0.000 asyncexitstack.py:15(__call__)
   16000    0.005    0.000    0.969    0.000 routing.py:656(__call__)
   16000    0.013    0.000    0.964    0.000 routing.py:2670(app)
```

`baseline`'s cumulative top 15 has none of `_tasks.py:322(_run_coro)` or `base.py:139(coro)` in it at all — its chain goes straight from `events.py:92(_run)` into `applications.py`/`errors.py`/`exceptions.py` (the normal FastAPI/Starlette request path). `base_http` has an extra hop: `_run_coro` → `coro` sits *between* the event loop and the exception handler, and it accounts for **1.009s of the 1.950s total** — over half the request time is inside two frames baseline never runs.

### Step 5 — confirm it: is that frame really new, or did I misread the list?

`stats 15` only shows the top rows; a frame further down the baseline list could still exist. Rather than guess, ask `pstats` directly — every unique `(file, line, function)` key is available as `Stats.stats`, so a two-line check settles it:

```python
>>> import pstats
>>> for name in ["baseline", "base_http", "starlette"]:
...     s = pstats.Stats(f"{name}.pstats")
...     hits = [k for k in s.stats if k[0] == "base.py"]
...     print(name, len(hits), [h[2] for h in hits])
...
baseline 0 []
base_http 11 ['__init__', 'wrapped_receive', '__call__', 'call_next', 'receive_or_disconnect', 'wrap', 'send_no_error', 'coro', 'body_stream', '__init__', '__call__']
starlette 0 []
```

Zero frames from `starlette/middleware/base.py` in `baseline` or `starlette`, eleven distinct functions from it in `base_http`. That's not a rounding difference in an existing code path — it's a whole extra module's worth of machinery that only runs when `BaseHTTPMiddleware` is in the stack.

### Step 6 — walk the call graph to find out *why* those frames run

`stats` tells you a frame exists; `callers`/`callees` tell you who calls it and what it calls, which is how you turn "there's a `coro` in there" into an actual mechanism. Start from the one line in the app that we know changed — `CustomHeaderMiddleware.dispatch()`, which calls `call_next()`:

```shell
base_http.pstats% callers dispatch
Function             was called by...
                         ncalls  tottime  cumtime
app.py:90(dispatch)  <-    6000    0.004    0.158  base.py:101(__call__)

base_http.pstats% callees call_next
Function                called...
                            ncalls  tottime  cumtime
base.py:112(call_next)  ->    2000    0.003    0.066  _tasks.py:137(start_soon)
                              2000    0.001    0.003  base.py:205(__init__)
                              6000    0.014    0.062  memory.py:115(receive)
                              2000    0.000    0.000  {method 'get' of 'dict' objects}

base_http.pstats% callers coro
Function                       was called by...
                                   ncalls  tottime  cumtime
base.py:139(coro)              <-   16000    0.007    1.009  _tasks.py:322(_run_coro)
```

`app.py:90` is our own `dispatch()` method — line 90 in `app_files/app.py` is exactly `async def dispatch(self, request, call_next):`. Reading the three snippets together: `dispatch()` calls `call_next()`, which calls `_tasks.py:137(start_soon)` — **spawning a new task** — and then blocks on `memory.py:115(receive)`, waiting for a result to arrive through a memory-object stream. The spawned task is what runs `base.py:139(coro)`, driven independently by `_tasks.py:322(_run_coro)` under its own `Context.run()`. That's the second `Context.run` and the second set of `_run_once` wake-ups spotted back in Step 3: `call_next()` doesn't call the rest of the app directly, it launches it as a sibling task and waits for the answer to be handed back across a queue.

### Step 7 — same walk for the request body

The `requests.py:254(body)` / `requests.py:234(stream)` frames from Step 4's baseline-vs-base_http diff get the same treatment:

```shell
base_http.pstats% callers receive_or_disconnect
Function                            was called by...
                                        ncalls  tottime  cumtime
base.py:113(receive_or_disconnect)  <-    4000    0.008    0.263  requests.py:234(stream)
```

`BaseHTTPMiddleware` hands `dispatch()` a `Request` object, but the ASGI layer underneath only ever gave it a `receive` callable. To make `request.stream()` / `request.body()` work inside `dispatch()`, it has to re-wrap `receive` (`base.py:113(receive_or_disconnect)`) and replay it — a second read of the body that the baseline, which never constructs that `Request` object, doesn't need.

### Step 8 — run the ASGI middleware as a control

If the theory is right — the tax comes from `BaseHTTPMiddleware`'s task-plus-stream design, not from "having any middleware at all" — then a plain ASGI middleware that touches the same header should look like baseline. `STARLETTECustomHeaderMiddleware` (see [middleware.md](middleware#starlette-timing-middleware)) wraps `send` directly with no `BaseHTTPMiddleware` in between:

```shell
$ python -m pstats starlette.pstats
starlette.pstats% sort tottime
starlette.pstats% stats 10
Tue Sep 15 21:40:27 2026    starlette.pstats

         1437980 function calls (1403981 primitive calls) in 0.779 seconds
```

**1.44M calls, 0.78s** — matches baseline's 1.41M/0.78s, not base_http's 3.43M/1.95s. The same `base.py` check from Step 5 confirms it (`starlette 0 []`, above). And walking the call graph the same way as Step 6, but for our own middleware's `__call__` (`app.py:140` in `app_files/app.py`):

```shell
starlette.pstats% callers app.py:140
Function              was called by...
                          ncalls  tottime  cumtime
app.py:140(__call__)  <-    8000    0.004    0.564  errors.py:149(__call__)

starlette.pstats% callees app.py:140
Function              called...
                          ncalls  tottime  cumtime
app.py:140(__call__)  ->    8000    0.006    0.561  exceptions.py:47(__call__)
```

One call in, one call out, no task spawn, no memory stream — `errors.py:149` calls straight into our middleware, which calls straight into `exceptions.py:47`, exactly one link in the same chain baseline already runs. That's the entire mechanical difference between the two middleware styles: `BaseHTTPMiddleware` detours through a second task and two stream re-reads to hand you a `Request`/`Response` API; a plain ASGI middleware is just another frame on the same call stack.

## Side by side

| | Baseline | BaseHTTPMiddleware | Starlette ASGI |
|---|---|---|---|
| Function calls (2000 req) | 1,413,940 | 3,434,000 (+2.4x) | 1,437,980 (+1.7%) |
| Wall time | 0.782s | 1.950s (+2.5x) | 0.779s (-0.4%) |
| `select.epoll` polls | 8,000 | 30,000 (+3.75x) | 8,000 (+0%) |
| Frames from `starlette/middleware/base.py` | 0 | 11 | 0 |
| Our middleware's call shape | — | detour: `dispatch()` → `call_next()` → spawn task + memory stream | inline: one `__call__` frame between `errors.py` and `exceptions.py` |

This is the same story the [middleware page](middleware) tells with `ab` (BaseHTTPMiddleware: -35 to -44% throughput; Starlette ASGI: 0-4%) — cProfile just names the exact frames responsible instead of leaving it as a percentage.

## Visualizing with snakeviz

For anything with more hot spots than fits comfortably in a `stats` listing, [SnakeViz](https://jiffyclub.github.io/snakeviz/) turns a `.pstats` file into an interactive icicle/sunburst chart where rectangle width (or arc angle) is proportional to time spent:

```shell
pip install snakeviz
snakeviz base_http.pstats
```

In a notebook: `%load_ext snakeviz` then `%snakeviz main()`. The CI `profiling` job already dumps a `.pstats` file per run (`PSTATS_OUT=...`) into the `Profiling-<python-version>` artifact used throughout this page — the BaseHTTPMiddleware run's icicle chart makes the doubled `base.py`/`_tasks.py` branch obvious at a glance next to the flat baseline, which is a faster way to spot the same thing Step 4 found by reading text.

## Conclusion

The methodology, generalized beyond this one comparison:

1. **Hold everything constant except the one thing you're testing** (Step 1) — otherwise you can't tell the profiler's diff from noise.
2. **Read the one-line summary before any row** (Step 2) — ncalls and total time already tell you whether there's a real difference worth chasing.
3. **Sort by `tottime` to find what's hot**, but expect generic runtime frames (event loop, GC, locks) at the top rather than an answer (Step 3).
4. **Sort by `cumtime` and diff against a baseline profile** to find call chains — and specific frames — that don't exist without the change (Step 4-5).
5. **Use `callers`/`callees` to walk outward from those frames** until you reach a line of code you actually wrote (Step 6-7) — that's what turns "there's a `coro` in there" into "our `dispatch()` calls `call_next()`, which spawns a task".
6. **Re-run the same profile with the suspected cause removed (or swapped) as a control** (Step 8) to confirm the theory, not just illustrate it.

For this repo's `BaseHTTPMiddleware` vs Starlette ASGI comparison, that process lands on a concrete mechanism: `BaseHTTPMiddleware.call_next()` runs the rest of the app as a second task and shuttles the request body and response through memory-object streams so it can hand `dispatch()` a `Request`/`Response` API, instead of letting the middleware sit inline on the same call stack like a plain ASGI class does. That's a fixed, structural cost — present regardless of what your `dispatch()` does — and it's exactly what the [measured throughput numbers](middleware) on the middleware page are paying for.
