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

### Small pool (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Large pool

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## Asynchronous endpoint with external API call

### Small pool (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Large pool

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## No external call vs small pool (sync)

### No external call (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Small pool with external call

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## No external call vs small pool (async)

### No external call (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Small pool with external call

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## Observations

* To be filled after CI run completes

## Verdict

Connection pool sizing is critical for applications making external API calls:
- A **small pool** (2 connections) creates a bottleneck when handling concurrent requests, as workers block waiting for available connections
- A **large pool** (100 connections) eliminates the connection bottleneck but uses more memory
- The impact is more pronounced with **synchronous** endpoints, where blocking the worker thread compounds the wait time
- For **asynchronous** endpoints, the event loop can handle other requests while waiting for a connection, reducing the impact of pool exhaustion
