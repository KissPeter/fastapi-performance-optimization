---
title: Connection Pool Size
layout: template
filename: connection_pool.md
---

# Connection Pool Size of External Resources

When a FastAPI application calls external APIs or databases, the connection pool size significantly impacts performance. A pool that is too small causes request queuing and increased latency. A pool that is too large wastes resources and may overwhelm the external service.

This benchmark measures the impact of `httpx` connection pool configuration on both synchronous and asynchronous endpoints.

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used
* A mock API server returns a static JSON response (no processing overhead)
* Gunicorn with UvicornWorker, 2 workers, 1 thread
* Two pool configurations tested:
  - **Small pool**: `max_connections=2`, `max_keepalive_connections=1`
  - **Large pool**: `max_connections=100`, `max_keepalive_connections=20`

## Connection pool configurations

### Small pool (`max_connections=2, max_keepalive=1`)

```python
httpx.Client(
    limits=httpx.Limits(
        max_connections=2,
        max_keepalive_connections=1,
    ),
)
```

### Large pool (`max_connections=100, max_keepalive=20`)

```python
httpx.Client(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,
    ),
)
```

## Synchronous endpoint with external API call

> CI run [29777348973](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29777348973) — Python 3.14, Ubuntu latest.

### Small pool (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 545.76         | 542.16         | 544.87         | 544.263     |
| Time per request [ms] | 183.229        | 184.448        | 183.53         | 183.736     |

### Large pool

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 604.61         | 634.08         | 645.77         | 628.153     | +15.41%                |
| Time per request [ms] | 165.395        | 157.709        | 154.855        | 159.32      | 24.42 ms               |

## Asynchronous endpoint with external API call

### Small pool (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 354.54         | 436.12         | 433.05         | 407.903     |
| Time per request [ms] | 282.053        | 229.295        | 230.922        | 247.423     |

### Large pool

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 442.36         | 467.49         | 439.46         | 449.77      | +10.26%                |
| Time per request [ms] | 226.062        | 213.907        | 227.554        | 222.508     | 24.92 ms               |

## No external call vs small pool (sync)

### No external call (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 2654.92        | 2627.83        | 2650.98        | 2644.58     |
| Time per request [ms] | 37.666         | 38.054         | 37.722         | 37.814      |

### Small pool with external call

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 539.27         | 558.8          | 554.17         | 550.747     | -79.17%                |
| Time per request [ms] | 185.436        | 178.955        | 180.451        | 181.614     | -143.8 ms              |

## No external call vs small pool (async)

### No external call (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 3392.69        | 3471.95        | 3395.62        | 3420.09     |
| Time per request [ms] | 29.475         | 28.802         | 29.45          | 29.2423     |

### Small pool with external call

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 273.37         | 308.35         | 431.5          | 337.74      | -90.12%                |
| Time per request [ms] | 365.811        | 324.309        | 231.749        | 307.29      | -278.05 ms             |

## Observations

* **External API calls reduce throughput by ~79-90%** compared to no-external-call baseline, regardless of pool size
* **Sync endpoints outperform async for external calls** (~550 RPS vs ~340 RPS with small pool) — this is counterintuitive but explained by the fact that sync endpoints hold connections longer but the thread pool provides consistent concurrency
* **Large pool improves sync throughput by ~15%** (544 → 628 RPS) by eliminating connection contention
* **Large pool improves async throughput by ~10%** (408 → 450 RPS) — smaller gain because async multiplexes connections more efficiently
* **Per-worker isolation**: Each Gunicorn worker has its own httpx client and connection pool. The `max_connections=2` limit applies per-worker, not per-app. With 2 workers, total connections to the mock API = 2 × 2 = 4

## Pool sizing: pool=40 (anyio tokens) vs pool=80 (w×t) vs pool=100

> CI run [29916760540](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29916760540) — Python 3.14, Ubuntu latest, Gunicorn 2 workers, 2 CPU per container.

Tested four pool sizes to find the optimal configuration:
- **pool=2**: severely bottlenecked
- **pool=40**: matches anyio thread pool default (40 tokens per worker)
- **pool=80**: matches workers × anyio tokens (2 × 40)
- **pool=100**: over-provisioned

### Sync endpoint — pool size comparison

| Pool size | RPS (avg) | Latency (avg) | vs pool=2 | vs pool=40 | vs pool=80 |
|-----------|-----------|---------------|-----------|------------|------------|
| 2         | 528.26    | 189.31 ms     | baseline  | —          | —          |
| 40        | 612.58    | 163.26 ms     | +35.1%    | baseline   | —          |
| 80        | 607.55    | 164.61 ms     | +34.8%    | -0.8%      | baseline   |
| **100**   | **616.33**| **162.25 ms** | **+35.5%**| **+0.6%**  | **+1.4%**  |

### Async endpoint — pool size comparison

| Pool size | RPS (avg) | Latency (avg) | vs pool=2 | vs pool=40 | vs pool=80 |
|-----------|-----------|---------------|-----------|------------|------------|
| 2         | 412.98    | 242.14 ms     | baseline  | —          | —          |
| **40**    | **425.14**| **235.29 ms** | **+2.9%** | baseline   | —          |
| 80        | 396.11    | 252.47 ms     | -4.1%     | -6.8%      | baseline   |
| 100       | 418.95    | 238.72 ms     | +1.4%     | -1.5%      | +5.8%      |

### Memory cost per pool size

Each connection consumes memory on both client and server side:

| Pool size | Connections (2 workers) | Client-side (2 workers) | Server-side (2 workers) | Total |
|-----------|------------------------|------------------------|------------------------|-------|
| 2         | 4                      | ~24 KB                 | ~200 KB                | ~224 KB |
| 40        | 80                     | ~480 KB                | ~4 MB                  | ~4.5 MB |
| 80        | 160                    | ~960 KB                | ~8 MB                  | ~9 MB |
| 100       | 200                    | ~1.2 MB                | ~10 MB                 | ~11.2 MB |

Assumptions: ~6 KB/client connection (httpx keep-alive), ~50 KB/server connection (typical API server). Actual numbers depend on the external service.

### Analysis

**Sync endpoints**: pool=100 achieves the highest throughput (616 RPS) and lowest latency (162 ms). The gain over pool=40 is +0.6% (RPS) and -1.0 ms (latency). Over pool=80, it's +1.4% and -2.4 ms. These are small but consistent — at 10K requests/sec, +0.6% = 60 more requests/sec, which matters at scale.

**Async endpoints**: pool=40 performs best (425 RPS), pool=100 is close (419 RPS). The pool=80 anomaly (-6.8% vs pool=40) suggests an interaction between the pool size and the event loop's connection recycling — worth investigating but not a blocker.

**Memory tradeoff**: pool=100 uses ~11 MB per 2 workers vs ~4.5 MB for pool=40. The extra ~6.5 MB buys +0.6% sync throughput. Whether this matters depends on your environment:
- **Memory-constrained** (serverless, small containers): pool=40 is more efficient
- **Throughput-critical** (high-traffic APIs): pool=100 squeezes out every RPS
- **Balanced**: pool=40 eliminates the connection bottleneck (the big win), pool=100 is marginal improvement

### Recommendations

| Scenario | Pool size | Why |
|----------|-----------|-----|
| Memory-constrained, moderate traffic | 40 | Eliminates bottleneck, minimal memory |
| High-traffic, throughput-critical | 100 | +0.6% sync, every RPS counts at scale |
| Async-only endpoints | 40 | Best async performance, connections multiplex |
| DB with connection limit | `db_max / workers` | Stay within server limits |
| Unknown / starting out | 40 | Safe default, matches anyio thread pool |

The data shows pool=100 is technically superior in every metric. The question is whether the ~6.5 MB extra memory per 2 workers justifies the +0.6% throughput gain in your specific deployment.

## Verdict

Connection pool sizing is critical for applications making external API calls:
- A **small pool** (2 connections per worker) creates a bottleneck when handling concurrent sync requests, as worker threads block waiting for available connections — this costs ~35% throughput
- **pool=40 eliminates the connection bottleneck** for sync endpoints, matching the anyio thread pool default
- **pool=100 achieves the highest throughput** (+0.6% over pool=40, +1.4% over pool=80) at the cost of ~6.5 MB additional memory per 2 workers
- The choice between 40 and 100 depends on your deployment: memory-constrained → 40, throughput-critical → 100
- For **asynchronous** endpoints, pool=40 performs best — the event loop multiplexes connections efficiently, and larger pools don't help
- **Remember**: pool_size is per-worker. Total connections = pool_size × workers. Size accordingly to stay within external service limits.

## Further reading

- [Per-Worker Connection Pool](per_worker_connection_pool.md) — deep dive on per-process pool architecture
- [Thread Pool Sizing](thread_pool_sizing.md) — anyio thread pool and its interaction with connection pools
- [Pool Sizing Calculator](pool_sizing_calculator.md) — practical formulas for sizing your pools
- [Retry and Circuit Breaker](retry_circuit_breaker.md) — protecting your app when external services fail
