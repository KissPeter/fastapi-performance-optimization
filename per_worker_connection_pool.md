---
title: Per-Worker Connection Pool
layout: template
filename: per_worker_connection_pool.md
---

# Per-Worker Connection Pool

Connection pools in WSGI/ASGI applications are **per-process, not per-application**. This is a critical detail that affects sizing, total resource consumption, and production behavior.

## The architecture

```
Application (multi-process)
  │
  ├── Worker 1 (OS process)
  │     ├── httpx.Client instance A  →  pool_size connections
  │     ├── httpx.AsyncClient instance A  →  pool_size connections
  │     └── SQLAlchemy engine A  →  pool_size connections
  │
  ├── Worker 2 (OS process)
  │     ├── httpx.Client instance B  →  pool_size connections
  │     ├── httpx.AsyncClient instance B  →  pool_size connections
  │     └── SQLAlchemy engine B  →  pool_size connections
  │
  └── Worker N (OS process)
        └── ... same pattern
```

Each worker is an isolated process with its own memory space. Module-level globals (like `httpx.Client()`) are **not shared** between workers — they're copied at fork time.

## Why this matters

### Total connections to external service

```
total_connections = pool_size × workers
```

| Workers | Pool size | Total connections to DB/API |
|---------|-----------|----------------------------|
| 2       | 10        | 20                          |
| 4       | 10        | 40                          |
| 8       | 10        | 80                          |

If your database has a `max_connections=100` limit and you run 8 workers with pool_size=20, you'll hit 160 connections — and get connection errors.

### Memory consumption

Each connection consumes memory on both sides:

| Connection type | Client-side memory | Server-side memory |
|-----------------|-------------------|-------------------|
| HTTP (keep-alive) | ~1-5 KB | ~5-50 KB |
| PostgreSQL | ~2-10 KB | ~50-100 KB |
| Redis | ~1-3 KB | ~10-30 KB |
| MySQL | ~2-8 KB | ~30-80 KB |

With 8 workers × pool_size=20 PostgreSQL connections = 160 connections × ~80 KB = ~12.5 MB just for connection overhead.

## Sizing formula

### Sync endpoints (httpx.Client, SQLAlchemy sync)

Each sync request that makes an external call **holds a connection for the entire request duration**. The pool limits concurrent *connections*, not concurrent *handlers*. Handlers beyond the pool size queue for a connection slot but remain active.

```
pool_size = min(
    anyio_thread_tokens,      # default 40 — this is the ACTUAL handler concurrency limit
    max_concurrent_connections,  # how many simultaneous connections you need
    server_max_connections    # external service limit
)
```

**Practical approach:**
```
pool_size = expected_concurrent_connections + headroom (2-5)
```

The `headroom` accounts for connections in transitional states (connecting, closing, keep-alive).

**CI-verified**: Handler concurrency is limited by anyio thread pool (40 default), NOT by pool_size. A pool_size=2 still allows 10+ concurrent handlers — they just queue for connections.

### Async endpoints (httpx.AsyncClient, SQLAlchemy async)

Multiple coroutines share connections via the event loop. Connections are not held during `await` — they're returned to the pool when the coroutine yields.

```
pool_size = concurrent_requests / 2  (connections are shared)
```

Async pools can be smaller because connections are multiplexed across coroutines.

## httpx specifics

### Sync client (module-level)

```python
# This creates ONE client per worker process
_sync_client = httpx.Client(
    limits=httpx.Limits(
        max_connections=10,       # per-worker
        max_keepalive_connections=5,  # per-worker
    ),
)
```

- `max_connections`: total concurrent connections (active + idle)
- `max_keepalive_connections`: connections kept alive after request completes

### Async client (lifespan-scoped)

```python
async with httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=10,       # per-worker
        max_keepalive_connections=5,  # per-worker
    ),
) as client:
    app.state.async_client = client
```

Same limits, but connections are shared across async coroutines on the event loop.

## Common pitfalls

### 1. Forgetting the multiplier

```
"My DB allows 100 connections. I have 4 workers. Pool size 100 is fine!"
→ 4 × 100 = 400 connections → DB rejects connections
```

**Fix:** `pool_size = db_max_connections / workers`

### 2. Pool exhaustion under load

```
pool_size=5, 10 concurrent sync requests
→ 5 requests get connections, 5 wait → increased latency
```

**Important distinction**: The pool limits *connection* concurrency, not *handler* concurrency. Handlers block waiting for a pool slot but remain "active" from the worker's perspective. Handler concurrency is limited by the anyio thread pool (default 40 tokens per worker).

**CI-verified** (run 29907570007): With pool_size=2 and 2 workers, sending 20 concurrent requests showed max_concurrent=10 handlers per worker — the pool queued 8 requests waiting for connections, but all 10 were counted as active. The pool acts as a throttle, not a hard limit.

**Fix:** Match pool size to expected concurrent *connections* (not handlers), or use async endpoints.

### 3. Connection leaks

If your code doesn't properly close connections (e.g., in error paths), the pool drains over time.

**Fix:** Use context managers:
```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### 4. Keep-alive exhaustion

Connections in keep-alive state don't count against `max_connections` in some libraries, but they do consume server resources.

**Fix:** Set `max_keepalive_connections` appropriately and tune `keepalive_expiry`.

## Monitoring

### httpx

```python
# Check pool status
print(_sync_client._pool._connections)  # active connections
print(_sync_client._pool._available)    # idle connections
```

### SQLAlchemy

```python
from sqlalchemy import event

@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_rec, connection_proxy):
    print(f"Connection checked out. Pool size: {engine.pool.size()}")
```

## Recommendations

| Scenario | Pool size per worker | Keepalive |
|----------|---------------------|-----------|
| Low traffic, async endpoints | 5-10 | 5 |
| Moderate traffic, sync endpoints | 10-20 | 10 |
| High traffic, sync endpoints | 20-50 | 20 |
| Database (PostgreSQL/MySQL) | 5-15 | 5-10 |

Always verify: `pool_size × workers ≤ external_service_max_connections`

## Pool exhaustion behavior

When all connections in the pool are busy and a new request arrives, it waits up to `timeout` seconds (default 5s) for a connection to become available.

```python
# httpx client with 5s timeout (default)
client = httpx.Client(
    limits=httpx.Limits(
        max_connections=40,
        max_keepalive_connections=20,
        keepalive_expiry=5,
    ),
    timeout=5.0,  # <-- waits up to 5s for a pool slot
)
```

### What happens when the pool is exhausted

| Scenario | What happens | How to detect |
|----------|-------------|---------------|
| Pool full, timeout=5s | Request waits 5s, then returns `PoolTimeout` | `httpx.PoolTimeout` exception |
| Pool full, timeout=0s | Request fails immediately with `PoolTimeout` | `httpx.PoolTimeout` exception |
| Pool full, requests queue | Throughput drops, latency spikes | High p95/p99 latency in benchmarks |
| Pool full, all workers blocked | All workers wait for pool slots, throughput = 0 | Complete stall |

### Testing pool exhaustion

> CI run 29928705459 — pool exhaustion tests verified.

We test pool exhaustion by sending concurrent requests with pool=2 (exceeds pool capacity):

**Short timeout (5s):** With pool=2, timeout=5s, 10 concurrent requests with 3s delay each:
- 2 requests start immediately (3s each)
- Remaining 8 queue for pool slots
- After 5s timeout, queued requests receive timeout status
- **Result:** Timeouts: 2, OKs: 8 out of 10 — demonstrates timeout behavior under exhaustion

**Long timeout (60s):** With pool=2, timeout=60s, 4 concurrent requests with 2s delay each:
- All requests eventually get a pool slot (4 * 2s / 2 connections = 4s total)
- **Result:** All requests succeed — demonstrates that longer timeouts allow requests to queue through

### Key insight: handlers remain active during pool wait

When a handler waits for a pool slot, the **handler thread remains active** — it's not released back to the pool. This means:
- Handler concurrency ≠ connection concurrency
- 50 handlers can be active with only 40 connections
- Handlers that are waiting for pool slots are using a thread pool token
- This is why pool sizing must consider both connection pool AND thread pool

See [Thread Pool Sizing](thread_pool_sizing.md) for the full picture.
