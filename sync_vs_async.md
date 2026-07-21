---
title: Sync / Async API Endpoints
layout: template
filename: sync_vs_async.md
---

# Sync / Async API Endpoints

FastAPI supports both synchronous and asynchronous endpoint definitions. Understanding the performance difference between them is crucial for choosing the right approach.

In a typical deployment with Gunicorn + UvicornWorker, each worker runs an async event loop. A synchronous endpoint blocks the worker's thread during execution, while an asynchronous endpoint releases the event loop, allowing the worker to handle other requests concurrently.

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used
* Gunicorn with UvicornWorker, 2 workers, 1 thread

## Small request / response

### Synchronous endpoint (baseline)

> CI run [29777348973](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29777348973) — Python 3.14, Ubuntu latest.

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 2414.1         | 2619.07        | 2359.54        | 2464.24     |
| Time per request [ms] | 41.423         | 38.181         | 42.381         | 40.6617     |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 3329.68        | 3405.91        | 2964.08        | 3233.22     | +31.21%                |
| Time per request [ms] | 30.033         | 29.361         | 33.737         | 31.0437     | 9.62 ms                |

## Large response (1MB JSON)

### Synchronous endpoint (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 19.71          | 19.35          | 19.66          | 19.5733     |
| Time per request [ms] | 5072.48        | 5169.15        | 5086.12        | 5109.25     |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 19.76          | 19.27          | 19.26          | 19.43       | -0.73%                 |
| Time per request [ms] | 5060.69        | 5188.56        | 5191.25        | 5146.83     | -37.58 ms              |

## Observations

* To be filled after CI run completes

## Verdict

The performance difference between sync and async endpoints depends on the workload:
- For **CPU-bound** tasks with no I/O waiting, the difference is negligible
- For **I/O-bound** tasks (database calls, external API requests), async endpoints allow the worker to handle other requests while waiting, significantly improving throughput under load
