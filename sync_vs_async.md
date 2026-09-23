---
title: Sync / Async endpoint
description: "Sync vs async FastAPI endpoints: async wins by 20-33% for typical payloads, dropping to ~4% for 1MB CPU-bound responses."
layout: template
filename: sync_vs_async.md
---

# Sync / Async API Endpoints

A key design decision for a FastAPI service is how to define the endpoint functions: `def` (sync) or `async def` (async). This page measures the actual throughput difference between the two across all server runners.

> **TL;DR** Prefer `async def` endpoints. Async gives a **+20-33% throughput** win for typical payloads and even helps on 1MB responses (+4%). Sync is only justified for fundamentally CPU-bound work where threads hit the GIL.

## Verdict

> **Individual impact (Median): up to +33% throughput** by using async endpoints over sync endpoints when params are small.

**Use `async def` endpoints as default** — the async FastAPI implementation gives a consistent +20-33% throughput for typical API payloads. This is one of the easiest wins on this page: simply change `def` → `async def` in your route handlers.

When the response is a **large 1MB JSON**, the difference mostly disappears (+4% async). The bottleneck becomes CPU-bound serialization, not the event loop.

**Sync is justified** only when your code is fundamentally blocking or CPU-bound and threads cannot escape the GIL (see the Gunicorn thread test). Otherwise async endpoints are measurably faster.

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used

## Cross-runner comparison

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

The same sync/async comparison was repeated across all 10 server runner configurations to see whether the endpoint type interacts with the runner.

### Sync endpoint (`/sync/items/`)

| Runner | RPS | Median latency [ms] |
|--------|-----|---------------------|
| Gunicorn (1 worker, 0 threads) | 1408.86 | 70.99 |
| Gunicorn (2 workers, 0 threads) | 2102.94 | 47.58 |
| Gunicorn (1 worker, 1 thread) | 1415.21 | 70.69 |
| Gunicorn (2 workers, 1 thread) | 2111.69 | 47.37 |
| Gunicorn (1 worker, 2 threads) | 1392.29 | 71.84 |
| Gunicorn (2 workers, 2 threads) | 2068.54 | 48.39 |
| Uvicorn single | 1182.71 | 84.56 |
| Uvicorn (2 workers) | 1213.57 | 82.41 |
| FastAPI CLI (1 worker) | 1428.91 | 69.99 |
| FastAPI CLI (2 workers) | 2273.51 | 44.04 |

### Async endpoint (`/async/items/`)

| Runner | RPS | Median latency [ms] |
|--------|-----|---------------------|
| Gunicorn (1 worker, 0 threads) | 1705.74 | 58.74 |
| Gunicorn (2 workers, 0 threads) | 2664.84 | 37.53 |
| Gunicorn (1 worker, 1 thread) | 1734.10 | 57.67 |
| Gunicorn (2 workers, 1 thread) | 2659.98 | 37.62 |
| Gunicorn (1 worker, 2 threads) | 1721.13 | 58.10 |
| Gunicorn (2 workers, 2 threads) | 2682.76 | 37.29 |
| Uvicorn single | 1451.85 | 68.89 |
| Uvicorn (2 workers) | 1480.07 | 67.57 |
| FastAPI CLI (1 worker) | 1841.48 | 54.31 |
| FastAPI CLI (2 workers) | 3034.90 | 32.95 |

### Observations
* Async endpoints give +20-33% throughput across all runners
* Latency is reduced by ~11-15ms per request

## Large response (1MB JSON)

> CI run [29775132906](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29775132906) — Python 3.14, Ubuntu latest.

To see if the sync/async difference holds for CPU-bound serialization, one large (1MB) JSON response was measured.

### Sync endpoint (`/sync/big_json_response/`)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |             19.51 |             19.64 |             19.62 |        19.59 |
| Time per request [ms] |          5125.68 |          5091.15 |          5096.26 |    5104.36   |

### Async endpoint (`/async/big_json_response/`)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference vs sync   |
|-----------------------|------------------|------------------|------------------|---------------|----------------------|
| Requests per second   |             20.06 |             20.69 |             20.28 |       20.3433 | +3.85 %              |
| Time per request [ms] |          4984.04 |          4832.62 |          4930.58 |     4915.75   | 188.61 ms            |

### Observations
* Async still wins even on CPU-bound serialization (+4%)
* The 1MB JSON serialization is the dominant cost, not the framework

## Reproduce

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m sync_async
```