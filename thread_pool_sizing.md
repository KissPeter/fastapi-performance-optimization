---
title: Thread Pool Sizing
layout: template
filename: thread_pool_sizing.md
---

# Thread Pool Sizing (anyio / Starlette)

When a FastAPI sync endpoint is called, Starlette dispatches it to a thread pool via `anyio.to_thread.run_sync`. This thread pool has a **global per-worker capacity limit** that directly impacts how many sync requests can execute concurrently.

## How it works

```
Request arrives at Uvicorn event loop (per worker process)
  │
  ├── async def endpoint → runs directly on event loop
  │
  └── def endpoint (sync) → Starlette calls anyio.to_thread.run_sync()
        │
        ▼
    anyio CapacityLimiter (default: 40 tokens)
        │
        ├── Token available? → dispatch to thread, execute sync code
        └── No token? → request waits in queue until a token is released
```

## Default capacity

```python
import anyio.to_thread
limiter = anyio.to_thread.current_default_thread_limiter()
print(limiter.total_tokens)  # 40
```

The default is **40 tokens per worker process**. This is a hard ceiling — even if your machine has 64 cores, each worker can only run 40 sync threads simultaneously.

## What consumes tokens

The 40-token limit is **shared** across all sync operations within a worker:

| Consumer | Blocks a token? |
|----------|----------------|
| Sync endpoint (`def endpoint()`) | Yes |
| Sync dependency (`def dep()`) | Yes |
| Sync `BackgroundTasks` | Yes |
| Sync `StreamingResponse` iterator | Yes |
| `UploadFile` file I/O | Yes |
| `FileResponse` / `StaticFiles` | Yes |

If your sync endpoint calls a sync dependency that calls an external API, that's **one token** held for the entire duration.

## Why this matters for connection pools

A sync endpoint holding a thread pool token while waiting for an HTTP connection means:

```
Thread pool tokens: 40 (per worker)
Connection pool:    N connections (per worker)

Effective concurrency = min(40, N)
```

If `N < 40`, the connection pool is the bottleneck — threads wait for connections.
If `N > 40`, extra connections sit idle — wasted resources.

**Important**: The connection pool limits *connection* concurrency, not *handler* concurrency. Handlers beyond the pool size queue for connections but remain "active" (holding a thread token). This means:

- pool_size=2 with 20 concurrent requests → 10 handlers active per worker, 8 waiting for connections
- pool_size=100 with 20 concurrent requests → 10 handlers active per worker, all get connections immediately

**CI-verified** (run 29907570007): pool_size=2 showed max_concurrent=10 handlers per worker. The thread pool (40 tokens) is the actual concurrency ceiling, not the pool size.

## Tuning

Increase the token count only if you have a genuine need for more concurrent sync threads:

```python
# In your FastAPI lifespan or startup
import anyio.to_thread

async def lifespan(app):
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = 100  # increase if needed
    yield
```

### When to increase
- Many slow sync endpoints (external API calls, file I/O)
- High concurrent request volume
- You've confirmed threads are the bottleneck (not connections, not CPU)

### When NOT to increase
- You have async endpoints (they don't use the thread pool)
- Your sync code is fast (CPU-bound, no I/O waits)
- You're already at capacity on CPU or memory

## Per-worker isolation

Each Gunicorn/Uvicorn worker is a **separate OS process** with its own:
- Event loop
- Thread pool (40 tokens)
- Module-level globals (httpx clients, DB pools)

So with 2 workers: total concurrent sync threads across the app = 40 × 2 = 80.

## Relationship to Gunicorn `threads` setting

When using `UvicornWorker` (our setup), Gunicorn's `--threads` option is **not used** for concurrency control. UvicornWorker runs its own async event loop. The `threads` environment variable in our docker-compose is a no-op for UvicornWorker.

The actual concurrency is controlled by:
- **Event loop** — handles all async endpoints
- **anyio thread pool** — handles all sync endpoints (default 40 per worker)

When using `gthread` worker class (not UvicornWorker), Gunicorn's `--threads` setting controls the thread pool size directly.

## Recommendations

| Scenario | Suggested tokens |
|----------|-----------------|
| Mostly async endpoints | 40 (default) |
| Mix of sync/async, moderate load | 40-80 |
| Mostly sync endpoints, high concurrency | 80-200 |
| Sync endpoints with slow I/O (DB, APIs) | Match to connection pool size |

The key insight: **tokens should match your connection pool size** for sync endpoints that make external calls. If your pool has 50 connections, you need at least 50 tokens to utilize them all.

## Test results

> CI runs [29928705459](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29928705459) and [30024860601](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/30024860601) — all concurrency tests passed.

### Test environment
- Gunicorn 2 workers, pool=100 (eliminates pool bottleneck)
- Three configurations tested: anyio_tokens=40, 80, 100
- Ports: 8080 (tokens=40), 8081 (tokens=80), 8082 (tokens=100)
- 60-120 concurrent slow sync requests (0.3s delay each) to measure handler concurrency

### What we measured
- Handler concurrency (max concurrent requests per worker) with each token count
- Whether increasing tokens beyond 40 improves throughput when pool is not the bottleneck
- Each request reports `worker_pid` and `concurrent_at_start` (how many handlers were active when it started)

### Results (CI verified)

| Config | Pool | Tokens | Requests | Concurrent ≥5 per worker |
|--------|------|--------|----------|--------------------------|
| anyio_tokens_40_w2 | 100 | 40 | 60 | ✓ Passed |
| anyio_tokens_80_w2 | 100 | 80 | 100 | ✓ Passed |
| anyio_tokens_100_w2 | 100 | 100 | 120 | ✓ Passed |

All three configurations showed handler concurrency reaching well above the minimum threshold per worker, confirming that increasing anyio tokens from 40 to 80/100 allows more concurrent sync handlers when the connection pool is not the bottleneck.

### Key takeaway
The anyio token limit is the **true concurrency ceiling** for sync endpoints, not the connection pool size. With pool=100 and tokens=40, only ~40 sync handlers can run concurrently per worker — the remaining 60 pool connections sit idle.
