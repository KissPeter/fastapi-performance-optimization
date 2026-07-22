---
title: Pool Sizing Calculator
layout: template
filename: pool_sizing_calculator.md
---

# Connection Pool Sizing Calculator

A practical guide to calculating the right connection pool size for your FastAPI deployment.

## Inputs you need

| Parameter | How to determine |
|-----------|-----------------|
| `workers` | Gunicorn/Uvicorn worker count |
| `threads` | Threads per worker (for `gthread` worker class) |
| `async_pool` | Whether using async endpoints |
| `max_concurrent_requests` | Expected peak concurrent requests |
| `db_max_connections` | Database server connection limit |
| `external_services` | Number of external APIs/DBs you call |

## Formulas

### Sync endpoints (httpx.Client, SQLAlchemy sync)

Each sync request holds a connection for the entire request duration.

```
pool_size_per_worker = min(
    anyio_thread_tokens,           # default 40
    max_concurrent_requests,       # your expected concurrency
    db_max_connections / workers   # don't exceed DB limit
)
```

**Conservative default:**
```
pool_size_per_worker = 10 + 5 (headroom) = 15
```

**Aggressive (high concurrency):**
```
pool_size_per_worker = 40  # match anyio default
```

### Async endpoints (httpx.AsyncClient, SQLAlchemy async)

Connections are shared across coroutines. Multiple coroutines can use the same connection (not simultaneously, but sequentially during awaits).

```
pool_size_per_worker = concurrent_requests / 2
```

Async pools can be smaller because:
1. Connections are not held during `await`
2. Connections are returned to the pool when the coroutine yields
3. The event loop multiplexes connections efficiently

### Total connections to external service

```
total = pool_size_per_worker × workers
```

**Constraint:**
```
total ≤ external_service_max_connections
```

## Worked examples

### Example 1: Small API (2 workers, async endpoints)

```
workers: 2
endpoint_type: async
concurrent_requests: 50
db_max_connections: 100

pool_size_per_worker = 50 / 2 = 25
total = 25 × 2 = 50 ≤ 100 ✓
```

**Recommendation:** `max_connections=25, max_keepalive=10`

### Example 2: Medium API (4 workers, sync endpoints)

```
workers: 4
endpoint_type: sync
concurrent_requests: 100
db_max_connections: 200

pool_size_per_worker = min(40, 100, 200/4) = 40
total = 40 × 4 = 160 ≤ 200 ✓
```

**Recommendation:** `max_connections=40, max_keepalive=15`

### Example 3: High-traffic API (8 workers, mixed sync/async)

```
workers: 8
endpoint_type: mixed (60% async, 40% sync)
concurrent_requests: 500
db_max_connections: 300

# Async endpoints
async_pool = 300 / 2 = 150 per worker → too high
async_pool = min(150, 500/8) = 62 per worker

# Sync endpoints
sync_pool = min(40, 500×0.4/8) = min(40, 25) = 25 per worker

# DB constraint
total_sync = 25 × 8 = 200
total_async = 62 × 8 = 496 → exceeds DB limit!
```

**Fix:** Reduce async pool to `300/8 = 37` per worker.

**Recommendation:** `max_connections=37, max_keepalive=15`

### Example 4: Multiple external services

```
workers: 4
services:
  - PostgreSQL: max_connections=100
  - Redis: max_connections=512
  - External API: no limit (but rate-limited)

# PostgreSQL
pg_pool = 100 / 4 = 25 per worker

# Redis (connection is lightweight)
redis_pool = 50 per worker

# External API (rate-limited at 1000 RPS)
api_pool = 20 per worker
```

Each service gets its own pool with its own limits.

## Quick reference table

| Workers | Sync pool/worker | Async pool/worker | Total sync | Total async |
|---------|-----------------|-------------------|------------|-------------|
| 1       | 10-20           | 10-20             | 10-20      | 10-20       |
| 2       | 10-20           | 10-20             | 20-40      | 20-40       |
| 4       | 10-20           | 10-20             | 40-80      | 40-80       |
| 8       | 5-15            | 5-15              | 40-120     | 40-120      |
| 16      | 3-10            | 3-10              | 48-160     | 48-160      |

As workers increase, per-worker pool size should decrease to stay within external service limits.

## Monitoring and tuning

### Signs your pool is too small

- `httpx.PoolTimeout` exceptions
- Increased latency under load
- `connection pool exhausted` errors in logs
- Requests queuing in thread pool

### Signs your pool is too large

- High memory usage per worker
- External service reporting too many connections
- Idle connections being closed by server (keepalive timeout)
- No performance improvement when increasing pool size

### How to tune

1. Start with conservative values (10-15 per worker)
2. Load test with expected peak traffic
3. Monitor: connection usage, latency, error rates
4. Increase pool size if connections are the bottleneck
5. Decrease if memory or DB connections are the bottleneck

```python
# Monitor httpx pool
import httpx
client = httpx.Client()
# After load test:
print(f"Pool connections: {client._pool._connections}")
print(f"Pool available: {client._pool._available}")
```

## The formula cheat sheet

```
sync_pool  = min(40, concurrent_requests, db_max/workers) + headroom
async_pool = concurrent_requests / 2
total      = pool × workers ≤ db_max_connections

headroom = 2-5 (for connection state transitions)
```

When in doubt, start small and scale up based on measured performance.
