---
title: Server Runners Comparison
layout: template
filename: server_runners.md
---


# Server Runners Comparison

This benchmark compares different ways to run a FastAPI application in production:
- **Gunicorn** with UvicornWorker (the traditional approach)
- **Uvicorn** directly (the built-in ASGI server)
- **FastAPI CLI** (`fastapi run` command, which wraps Uvicorn internally)
- **Uvicorn with `--workers`** flag (Uvicorn's native multi-process mode)

All runners are tested with 1 and 2 workers to compare both single-process and multi-process performance.

## Server Runners

### Gunicorn with UvicornWorker
[Gunicorn](https://gunicorn.org/) is a mature WSGI HTTP server that can run ASGI applications via the [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) class. It acts as a process manager, spawning multiple Uvicorn worker processes. This has been the recommended production setup for FastAPI.

### Uvicorn
[Uvicorn](https://www.uvicorn.org/) is a lightning-fast ASGI server directly. Running it without `--workers` uses a single process. Gunicorn's documentation [suggests](https://www.uvicorn.org/deployment/#gunicorn) running behind Gunicorn for production.

### FastAPI CLI
[FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/) (`fastapi run`) is the official way to run FastAPI apps. Under the hood, it uses Uvicorn. With `--workers N`, it spawns N Uvicorn worker processes. This is the simplest way to get multi-process FastAPI running.

### Uvicorn with `--workers`
Uvicorn natively supports the `--workers` flag to spawn multiple worker processes, similar to how Gunicorn manages workers but without the Gunicorn overhead.

## Measurements

Both synchronous and asynchronous API endpoints were tested with 1 and 2 workers. The Gunicorn container is used as the baseline for comparison.

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Azure Linux, Ubuntu latest.

### Sync endpoint, 1 worker

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | 1636.94 | - |
| Uvicorn | 1445.94 | -11.67 % |
| FastAPI CLI | 1587.70 | -3.01 % |
| Uvicorn --workers | 1462.06 | -10.68 % |

### Async endpoint, 1 worker

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | 2794.80 | - |
| Uvicorn | 2168.70 | -22.40 % |
| FastAPI CLI | 2674.32 | -4.31 % |
| Uvicorn --workers | 2185.24 | -21.81 % |

### Sync endpoint, 2 workers

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | 2189.33 | - |
| Uvicorn | 1863.56 | -14.88 % |
| FastAPI CLI | 2401.51 | +9.69 % |
| Uvicorn --workers | 1848.68 | -15.56 % |

### Async endpoint, 2 workers

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | 3879.92 | - |
| Uvicorn | 3149.81 | -18.82 % |
| FastAPI CLI | 4325.95 | +11.50 % |
| Uvicorn --workers | 3411.15 | -12.08 % |

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

**FastAPI CLI (`fastapi run --workers`) is the clear winner with 2 workers** — it outperforms Gunicorn by ~10-12% on multi-worker setups while matching it closely at 1 worker (-3 to -4%). This makes sense: FastAPI CLI uses Uvicorn internally but with a lighter process management layer than Gunicorn.

**Gunicorn remains the best choice for 1-worker deployments**, beating all alternatives. Its process management overhead is negligible at low worker counts.

**Plain Uvicorn and Uvicorn `--workers`** consistently lag behind Gunicorn by 11-22%. The `--workers` flag does not close the gap — it performs similarly to plain Uvicorn, suggesting the bottleneck is in Uvicorn's core request handling, not process management.

The key takeaway: for production multi-worker FastAPI deployments, `fastapi run --workers N` is the simplest and fastest option.

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m server_runners
```
