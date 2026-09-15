---
title: Profiling
layout: template
filename: profiling.md
---

# Profiling your FastAPI application

Every other page in this project answers "how much faster" with `ab` load-test numbers. This page answers "why" with [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile), Python's built-in deterministic profiler. It's a good general primer credit goes to this [cProfile walkthrough](https://machinelearningplus.com/python/cprofile-how-to-profile-your-python-code/) — this page applies the same technique directly to this repo's app to explain the [BaseHTTPMiddleware vs Starlette ASGI middleware](middleware) result.

## Why profile instead of just load-testing

`ab` (and similar tools) tell you throughput and latency dropped. They don't tell you *where* the time went — which function, called how many times, at what depth of the call stack. cProfile does. Point it at a piece of code and it counts, for every function called:

* **ncalls** — how many times it was called (`x/y` means `y` primitive calls, `x` total including recursion)
* **tottime** — time spent in the function itself, excluding sub-calls
* **cumtime** — time spent in the function *and* everything it calls
* **percall** — the above divided by ncalls

`tottime` tells you what's actually slow; `cumtime` tells you which call path is expensive. When a load test shows a regression, cProfile shows the extra frames responsible for it.

## Test environment

> CI run [35014905057](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/35014905057) — Python 3.14, Ubuntu latest, `profiling` job.

* Same dependency pins as this CI run: FastAPI 0.139.2, Starlette 1.3.1, httpx 0.28.1
* The profiler is pointed at `app_files/app.py`'s ASGI callable directly, bypassing the HTTP client/server entirely, so it isolates middleware overhead from network and test-tooling overhead
* Script: [`test_files/profile_middleware.py`](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/profile_middleware.py) — reproduce locally with:
```shell
MODE=baseline  python3 test_files/profile_middleware.py   # no middleware
MODE=base_http python3 test_files/profile_middleware.py   # BaseHTTPMiddleware
MODE=starlette python3 test_files/profile_middleware.py   # Starlette ASGI middleware
```
* The same three runs execute in CI on every push (job `profiling` in [`performance_tuning_measurements.yml`](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/.github/workflows/performance_tuning_measurements.yml)), each uploaded as a `Profiling-<python-version>` artifact containing both the `pstats` dumps and the `print_stats()` text output — the tables below are the text output from that artifact, unedited

## Profiling the app directly

The simplest way to profile a function or a block of code is `cProfile.run()`:

```python
import cProfile
cProfile.run("20 + 10")
```

For anything beyond a one-liner, the `Profile` class gives more control, and [`pstats`](https://docs.python.org/3/library/profile.html#pstats.Stats) lets you sort and print the results however you like:

```python
import cProfile, pstats

profiler = cProfile.Profile()
profiler.enable()
main()                       # the code you want to measure
profiler.disable()

stats = pstats.Stats(profiler).sort_stats("tottime")
stats.strip_dirs()           # drop noisy absolute paths from output
stats.print_stats(25)        # top 25 rows
```

Since FastAPI request handling is async, `profiler.enable()` / `disable()` must wrap the event loop that drives the ASGI app, not a synchronous call — `test_files/profile_middleware.py` builds a minimal ASGI `scope`/`receive`/`send` triple, calls `app(scope, receive, send)` 2000 times inside one `asyncio.run()`, and profiles that loop. This avoids pulling `TestClient`'s own thread-portal machinery into the profile, which would otherwise dominate `tottime` and hide the actual middleware cost.

## Baseline: no middleware

```
1413940 function calls (1379943 primitive calls) in 0.782 seconds

Ordered by: internal time

  ncalls  tottime  percall  cumtime  percall filename:lineno(function)
20000/2000 0.035    0.000    0.070    0.000 encoders.py:129(jsonable_encoder)
    8000    0.035    0.000    0.446    0.000 routing.py:399(app)
8001/8000  0.033    0.000    0.715    0.000 base_events.py:1977(_run_once)
  142000    0.022    0.000    0.025    0.000 {built-in method builtins.isinstance}
    8000    0.018    0.000    0.130    0.000 _asyncio.py:2649(run_sync_in_worker_thread)
    8000    0.018    0.000    0.018    0.000 {method 'poll' of 'select.epoll' objects}
    2000    0.017    0.000    0.073    0.000 utils.py:598(solve_dependencies)
```

2000 requests cost **1.41M function calls** and **0.78s**. The event loop woke up **8000** times (`select.epoll` on the Ubuntu CI runner) — 4 per request, which lines up with a normal request: read the socket, run the sync endpoint in the thread pool, write the response, and one bookkeeping cycle.

## BaseHTTPMiddleware: one `dispatch()` that adds a header

Same endpoint, same payload, with the [`CustomHeaderMiddleware`](middleware#with-two-middlewares) from the middleware page added (`app.add_middleware(CustomHeaderMiddleware)`, a `BaseHTTPMiddleware` subclass):

```
3434000 function calls (3380000 primitive calls) in 1.950 seconds

Ordered by: internal time

  ncalls  tottime  percall  cumtime  percall filename:lineno(function)
30001/30000 0.103   0.000    1.878    0.000 base_events.py:1977(_run_once)
54000/52000 0.047   0.000    1.647    0.000 {method 'run' of '_contextvars.Context' objects}
   10000    0.043    0.000    0.776    0.000 routing.py:399(app)
   30000    0.040    0.000    0.040    0.000 {method 'poll' of 'select.epoll' objects}
20000/2000 0.039    0.000    0.076    0.000 encoders.py:129(jsonable_encoder)
  176000    0.031    0.000    0.038    0.000 {built-in method builtins.isinstance}
   42000    0.031    0.000    0.058    0.000 base_events.py:847(_call_soon)
    4000    0.027    0.000    0.101    0.000 _asyncio.py:862(_spawn)
   10000    0.021    0.000    0.329    0.000 base.py:101(__call__)
    6000    0.019    0.000    0.135    0.000 base.py:119(wrap)
```

Sorted by cumulative time, the extra frames that don't exist in the baseline at all show up right where the request enters the middleware:

```
   20000    0.015    0.000    1.054    0.000 _tasks.py:322(_run_coro)
   16000    0.007    0.000    1.002    0.000 base.py:139(coro)
   10000    0.021    0.000    0.327    0.000 base.py:101(__call__)
    6000    0.010    0.000    0.283    0.000 requests.py:254(body)
12000/10000 0.010    0.000    0.268    0.000 requests.py:234(stream)
    4000    0.008    0.000    0.261    0.000 base.py:113(receive_or_disconnect)
```

2000 requests now cost **3.43M function calls** and **1.95s** — 2.4x the calls, 2.5x the time, for a middleware that does nothing but set one response header. The `select.epoll` poll count went from 8000 to **30000**: 3.75x more event-loop wake-ups per request.

### Why: `BaseHTTPMiddleware` runs your endpoint in a second task

`base.py:101(__call__)`, `base.py:119(wrap)`, `base.py:139(coro)` are [`starlette/middleware/base.py`](https://github.com/encode/starlette/blob/master/starlette/middleware/base.py). `BaseHTTPMiddleware.dispatch()` needs to hand you a `Request`/`Response` pair instead of raw ASGI messages, so `call_next()` can't just call the downstream app inline — it has to:

1. Spawn the rest of the app (`app.py:2670`, your endpoint, response serialization) as a **separate task** (`_asyncio.py:862(_spawn)`, `_tasks.py:322(_run_coro)`)
2. Re-read the incoming request body through an async generator (`requests.py:234(stream)` / `254(body)`) so your `dispatch()` can see it as a `Request` object
3. Shuttle the response back through a memory object stream (`receive_or_disconnect`) so it can be exposed to you as a `Response` you're allowed to mutate before it's actually sent

Two coroutines now have to hand data back and forth instead of one coroutine calling straight through, and every hand-off is a suspension point the event loop has to schedule — hence the 3.75x jump in `select.epoll` polls. This is a fixed per-request tax that exists purely because of *how* `BaseHTTPMiddleware` is built, independent of what your `dispatch()` actually does.

## Starlette ASGI middleware: same header, no `BaseHTTPMiddleware`

Same test, with [`STARLETTECustomHeaderMiddleware`](middleware#starlette-timing-middleware) — a plain ASGI class that wraps `send` directly, no `BaseHTTPMiddleware`:

```
1437980 function calls (1403981 primitive calls) in 0.779 seconds

Ordered by: internal time

  ncalls  tottime  percall  cumtime  percall filename:lineno(function)
20000/2000 0.036    0.000    0.070    0.000 encoders.py:129(jsonable_encoder)
    8000    0.035    0.000    0.441    0.000 routing.py:399(app)
8001/8000  0.032    0.000    0.716    0.000 base_events.py:1977(_run_once)
  142000    0.022    0.000    0.025    0.000 {built-in method builtins.isinstance}
    8000    0.018    0.000    0.128    0.000 _asyncio.py:2649(run_sync_in_worker_thread)
    8000    0.014    0.000    0.014    0.000 {method 'poll' of 'select.epoll' objects}
    2000    0.017    0.000    0.073    0.000 utils.py:598(solve_dependencies)
```

**1.44M function calls**, **0.78s**, and `select.epoll` back down to **8000** — statistically identical to the no-middleware baseline. There is no `base.py`, no `_spawn`, no second `requests.py:234(stream)` read. The whole `starlette/middleware/base.py` call chain is simply absent from the profile because the middleware never leaves the ASGI protocol: it wraps `send`, appends a header when it sees `http.response.start`, and gets out of the way.

## Side by side

| | Baseline | BaseHTTPMiddleware | Starlette ASGI |
|---|---|---|---|
| Function calls (2000 req) | 1,413,940 | 3,434,000 (+2.4x) | 1,437,980 (+1.7%) |
| Wall time | 0.782s | 1.950s (+2.5x) | 0.779s (-0.4%) |
| `select.epoll` polls | 8,000 | 30,000 (+3.75x) | 8,000 (+0%) |
| Extra frames vs baseline | — | `base.py` dispatch/wrap/coro, `requests.py` stream/body, `_tasks.py`/`_spawn` | none |

This is the same story the [middleware page](middleware) tells with `ab` (BaseHTTPMiddleware: -35 to -44% throughput; Starlette ASGI: 0-4%) — cProfile just names the culprit. The regression isn't the one line of code in `dispatch()`, it's the extra task and the two async-generator hops `BaseHTTPMiddleware` needs to expose a `Request`/`Response` API on top of raw ASGI.

## Visualizing with snakeviz

For anything with more than a handful of hot spots, a flat `print_stats()` table gets hard to read. [SnakeViz](https://jiffyclub.github.io/snakeviz/) turns a dumped profile into an interactive icicle/sunburst chart where rectangle width (or arc angle) is proportional to time spent:

```shell
pip install snakeviz
python3 -c "
import cProfile
cProfile.run('main()', 'profile.out')
"
snakeviz profile.out
```

In a notebook: `%load_ext snakeviz` then `%snakeviz main()`. `test_files/profile_middleware.py` accepts a `PSTATS_OUT` env var to dump the raw `pstats` file alongside the text report (this is what the CI `profiling` job does for each of the three runs, uploaded in the `Profiling-<python-version>` artifact):

```shell
MODE=base_http PSTATS_OUT=base_http.pstats python3 test_files/profile_middleware.py
snakeviz base_http.pstats
```

The BaseHTTPMiddleware run's icicle chart makes the doubled `base.py`/`_tasks.py` branch obvious at a glance next to the flat baseline.

## Conclusion

* cProfile turns a load-test regression into a concrete list of extra function calls, which is what actually lets you fix (or justify) a slowdown instead of guessing at it.
* For this repo's `BaseHTTPMiddleware` vs Starlette ASGI comparison, the profile confirms the [measured throughput numbers](middleware): the cost is structural (an extra task + two stream hops per request), not something you can dispatch your way around.
* When in doubt about *why* an optimization worked (or a regression appeared), profile before and after — the diff between the two `pstats` outputs is usually self-explanatory.
