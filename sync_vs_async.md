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
* Tested across all 10 server runner configurations

> CI run [29858316413](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29858316413) — Python 3.14, Ubuntu latest.

## Cross-runner comparison (small request / response)

| Runner | Sync RPS | Async RPS | Improvement | Sync Latency | Async Latency |
|--------|----------|-----------|-------------|-------------|---------------|
| Gunicorn (1 worker, 0 threads) | 1410.94 | 1767.42 | **+25.26%** | 70.89 ms | 56.58 ms |
| Gunicorn (2 workers, 0 threads) | 2171.56 | 2650.26 | **+22.04%** | 46.05 ms | 37.76 ms |
| Gunicorn (1 worker, 1 thread) | 1428.34 | 1775.63 | **+24.31%** | 70.02 ms | 56.32 ms |
| Gunicorn (2 workers, 1 thread) | 2147.73 | 2781.01 | **+29.49%** | 46.57 ms | 35.96 ms |
| Gunicorn (1 worker, 2 threads) | 1400.94 | 1741.95 | **+24.34%** | 71.41 ms | 57.41 ms |
| Gunicorn (2 workers, 2 threads) | 2116.36 | 2722.99 | **+28.66%** | 47.26 ms | 36.72 ms |
| Uvicorn single-process | 1209.30 | 1458.78 | **+20.63%** | 82.71 ms | 68.55 ms |
| Uvicorn --workers (2 workers) | 1799.88 | 2224.70 | **+23.60%** | 55.59 ms | 44.97 ms |
| FastAPI CLI (1 worker) | 1448.24 | 1853.47 | **+27.98%** | 69.05 ms | 53.95 ms |
| FastAPI CLI (2 workers) | 2267.33 | 3004.70 | **+32.52%** | 44.15 ms | 33.38 ms |

### Observations

* **Async consistently wins by 20-33%** across all runner configurations
* **Largest async benefit: FastAPI CLI 2 workers (+32.52%) and Gunicorn 2 workers, 1 thread (+29.49%)** — runners with 2 workers benefit more from async because the event loop can handle more concurrent connections per worker
* **Smallest async benefit: Uvicorn single-process (+20.63%)** — single worker limits concurrency gains
* The improvement is **consistent regardless of threads** — adding threads to Gunicorn (t0 vs t1 vs t2) doesn't change the async advantage significantly
* **Higher absolute throughput with 2 workers**: Gunicorn (2 workers), FastAPI CLI (2 workers), and Uvicorn --workers (2 workers) all outperform their 1-worker counterparts for both sync and async

## Large response (1MB JSON)

> CI run [29815274014](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29815274014) — Gunicorn (2 workers, 0 threads) only.

When the response payload is large (1MB), the bottleneck shifts to serialization and network transfer. The async event loop advantage largely disappears.

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

### Observations (large response)
* **Async advantage drops to ~4%** — negligible compared to 20-33% for small responses
* Serialization of the 1MB payload dominates the request time, masking the event loop efficiency gain
* Latency still improves by ~192ms, but throughput barely changes

## Verdict

> **Individual impact: +20-33% throughput** by switching from sync to async endpoints.

Use **async endpoints** (`async def`) as the default for FastAPI applications. The performance benefit is significant for typical API workloads (small/medium responses) and zero cost for large payloads.

The advantage is most pronounced when endpoints perform I/O operations (database queries, external API calls, file reads). For purely CPU-bound endpoints (image processing, heavy computation), the difference narrows.

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m sync_async
```
