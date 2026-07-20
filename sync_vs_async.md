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

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## Large response (1MB JSON)

### Synchronous endpoint (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | -              | -              | -              | -           |
| Time per request [ms] | -              | -              | -              | -           |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | -              | -              | -              | -           | -                      |
| Time per request [ms] | -              | -              | -              | -           | - ms                   |

## Observations

* To be filled after CI run completes

## Verdict

The performance difference between sync and async endpoints depends on the workload:
- For **CPU-bound** tasks with no I/O waiting, the difference is negligible
- For **I/O-bound** tasks (database calls, external API requests), async endpoints allow the worker to handle other requests while waiting, significantly improving throughput under load
