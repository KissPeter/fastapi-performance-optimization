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
* Gunicorn with UvicornWorker, 2 workers, 0 threads

> CI run [29815274014](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29815274014) — Python 3.14, Ubuntu latest.

## Small request / response

### Synchronous endpoint (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 2632.75        | 2611.62        | 2481.24        | 2575.2      |
| Time per request [ms] | 37.983         | 38.29          | 40.302         | 38.8583     |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 3529.66        | 3334.75        | 3328.7         | 3397.7      | +31.94%                |
| Time per request [ms] | 28.331         | 29.987         | 30.042         | 29.4533     | 9.41 ms                |

## Large response (1MB JSON)

### Synchronous endpoint (baseline)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 18.84          | 19.19          | 19.6           | 19.21       |
| Time per request [ms] | 5307.4         | 5209.97        | 5103.06        | 5206.81     |

### Asynchronous endpoint

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline |
|-----------------------|----------------|----------------|----------------|-------------|------------------------|
| Requests per second   | 19.65          | 20.03          | 20.15          | 19.9433     | +3.82%                 |
| Time per request [ms] | 5090.03        | 4991.68        | 4963.7         | 5015.14     | 191.67 ms              |

## Observations

* **Small responses: async wins by ~32%.** The async endpoint handles 3398 RPS vs 2575 RPS for sync. The event loop can process other requests while waiting for I/O, effectively multiplexing work within each worker.
* **Large responses: difference is negligible (~4%).** When the response is 1MB, the bottleneck shifts to serialization and network transfer. The event loop advantage disappears because the CPU is busy serializing the large payload.
* **Latency improvement is consistent** — async reduces per-request latency by ~9ms for small responses and ~192ms for large responses, even though throughput barely changes for large payloads.

## Verdict

Use **async endpoints** (`async def`) as the default for FastAPI applications. The performance benefit is significant for typical API workloads (small/medium responses) and zero cost for large payloads.

The advantage is most pronounced when endpoints perform I/O operations (database queries, external API calls, file reads). For purely CPU-bound endpoints (image processing, heavy computation), the difference narrows.

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m sync_async
```
