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

* To be filled after CI run completes

## Verdict

Connection pool sizing is critical for applications making external API calls:
- A **small pool** (2 connections) creates a bottleneck when handling concurrent requests, as workers block waiting for available connections
- A **large pool** (100 connections) eliminates the connection bottleneck but uses more memory
- The impact is more pronounced with **synchronous** endpoints, where blocking the worker thread compounds the wait time
- For **asynchronous** endpoints, the event loop can handle other requests while waiting for a connection, reducing the impact of pool exhaustion
