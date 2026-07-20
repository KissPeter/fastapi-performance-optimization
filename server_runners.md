---
title: Server Runners Comparison
layout: template
filename: server_runners.md
---


# Server Runners Comparison

This benchmark compares three ways to run a FastAPI application in production, each tested with 1 and 2 workers:
- **Gunicorn** with UvicornWorker — WSGI process manager spawning Uvicorn workers
- **Uvicorn** with `--workers` — ASGI server with native multi-process mode
- **FastAPI CLI** (`fastapi run --workers`) — official FastAPI CLI wrapping Uvicorn

All runners use the same underlying ASGI server (Uvicorn). The difference is in process management and startup overhead.

## Server Runners

### Gunicorn with UvicornWorker
[Gunicorn](https://gunicorn.org/) is a mature WSGI HTTP server that runs ASGI applications via the [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) class. It acts as a process manager, spawning multiple Uvicorn worker processes. This has been the recommended production setup for FastAPI.

### Uvicorn with `--workers`
[Uvicorn](https://www.uvicorn.org/) natively supports the `--workers` flag to spawn multiple worker processes. Each worker is a standalone Uvicorn process. This is simpler than Gunicorn but lacks its process management features (graceful restarts, worker recycling, etc.).

### FastAPI CLI
[FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/) (`fastapi run --workers N`) is the official way to run FastAPI apps. Under the hood, it uses Uvicorn. With `--workers N`, it spawns N Uvicorn worker processes. This is the simplest way to get multi-process FastAPI running.

## Measurements

Both synchronous (`POST /sync/items/`) and asynchronous (`POST /async/items/`) endpoints were tested. The Gunicorn container is used as the baseline for comparison.

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

### Sync endpoint, 1 worker

| Runner (1 worker) | RPS | vs Gunicorn |
|--------------------|-----|-------------|
| Gunicorn (baseline) | 1636.94 | - |
| Uvicorn --workers | 1445.94 | -11.67 % |
| FastAPI CLI --workers | 1587.70 | -3.01 % |

### Async endpoint, 1 worker

| Runner (1 worker) | RPS | vs Gunicorn |
|--------------------|-----|-------------|
| Gunicorn (baseline) | 2794.80 | - |
| Uvicorn --workers | 2168.70 | -22.40 % |
| FastAPI CLI --workers | 2674.32 | -4.31 % |

### Sync endpoint, 2 workers

| Runner (2 workers) | RPS | vs Gunicorn |
|--------------------|-----|-------------|
| Gunicorn (baseline) | 2189.33 | - |
| Uvicorn --workers | 1863.56 | -14.88 % |
| FastAPI CLI --workers | 2401.51 | +9.69 % |

### Async endpoint, 2 workers

| Runner (2 workers) | RPS | vs Gunicorn |
|--------------------|-----|-------------|
| Gunicorn (baseline) | 3879.92 | - |
| Uvicorn --workers | 3149.81 | -18.82 % |
| FastAPI CLI --workers | 4325.95 | +11.50 % |

See [GitHub Actions](https://github.com/KissPeter/fastapi-performance-optimization/actions/workflows/performance_tuning_measurements.yml) for the latest results.

## Versions

| Package | Version |
|---------|---------|
| Python | 3.14 |
| FastAPI | 0.139.2 |
| Uvicorn | 0.51.0 |
| Gunicorn | 26.0.0 |
| orjson | 3.11.9 |
| ujson | 5.13.0 |

## Verdict

| Workers | Best Runner | RPS | Runner Advantage |
|---------|-------------|-----|------------------|
| 1 worker | Gunicorn | 1636 / 2794 (sync/async) | ~3-22% faster than alternatives |
| 2 workers | FastAPI CLI | 2401 / 4326 (sync/async) | ~10-12% faster than Gunicorn |

**With 1 worker**, Gunicorn wins across the board. Its process management overhead is negligible at low worker counts, and it consistently outperforms both Uvicorn and FastAPI CLI.

**With 2 workers**, FastAPI CLI (`fastapi run --workers`) pulls ahead by 10-12%. It uses the same Uvicorn workers under the hood but with a lighter startup path than Gunicorn's WSGI-to-ASGI bridge.

**Uvicorn `--workers`** consistently lags behind Gunicorn by 11-22%. Despite being pure ASGI (no WSGI bridge overhead), it doesn't match Gunicorn's performance, suggesting Gunicorn's worker management is more efficient.

**Recommendation**: Use `fastapi run --workers N` for multi-worker deployments. Use Gunicorn with UvicornWorker for single-worker setups or when you need Gunicorn's operational features (graceful restarts, worker recycling, resource limits).

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m server_runners
```
