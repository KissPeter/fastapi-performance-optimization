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

### Sync endpoint, 1 worker

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | TBD | - |
| Uvicorn | TBD | TBD |
| FastAPI CLI | TBD | TBD |
| Uvicorn --workers | TBD | TBD |

### Async endpoint, 1 worker

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | TBD | - |
| Uvicorn | TBD | TBD |
| FastAPI CLI | TBD | TBD |
| Uvicorn --workers | TBD | TBD |

### Sync endpoint, 2 workers

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | TBD | - |
| Uvicorn | TBD | TBD |
| FastAPI CLI | TBD | TBD |
| Uvicorn --workers | TBD | TBD |

### Async endpoint, 2 workers

| Runner | RPS | Difference to Gunicorn |
|--------|-----|----------------------|
| Gunicorn (baseline) | TBD | - |
| Uvicorn | TBD | TBD |
| FastAPI CLI | TBD | TBD |
| Uvicorn --workers | TBD | TBD |

> Results will be populated after CI run completes. See [GitHub Actions](https://github.com/KissPeter/fastapi-performance-optimization/actions/workflows/performance_tuning_measurements.yml) for the latest results.

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

Results pending CI execution. The key question is whether Gunicorn's process management overhead is worth the stability benefits compared to running Uvicorn directly or through FastAPI CLI.

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m server_runners
```
