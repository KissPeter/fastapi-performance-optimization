---
title: Server Runners Comparison
layout: template
filename: server_runners.md
---


# Server Runners Comparison

This benchmark compares five ways to run a FastAPI application in production:
- **Gunicorn** with UvicornWorker — WSGI process manager (1w/2w × 0t/1t/2t)
- **Uvicorn** — single-process ASGI server
- **Uvicorn with `--workers`** — ASGI server with native multi-process mode
- **FastAPI CLI** (`fastapi run --workers`) — official CLI wrapping Uvicorn with `--workers`

All runners use the same underlying ASGI server (Uvicorn). The difference is in how they manage processes and handle startup.

## Server Runners

### Gunicorn with UvicornWorker
[Gunicorn](https://gunicorn.org/) is a mature WSGI HTTP server that runs ASGI applications via the [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) class. It acts as a process manager, spawning multiple Uvicorn worker processes.

### Uvicorn (single process)
[Uvicorn](https://www.uvicorn.org/) is a lightning-fast ASGI server. Running it without `--workers` uses a single process.

### Uvicorn with `--workers`
Uvicorn natively supports the `--workers` flag to spawn multiple worker processes. Simpler than Gunicorn but lacks its process management features.

### FastAPI CLI
[FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/) (`fastapi run --workers N`) wraps Uvicorn with `--workers`.

## Measurements

> CI run [29815274014](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29815274014) — Python 3.14, Ubuntu latest.

### Gunicorn thread matrix

| Workers | Threads | Sync RPS | Async RPS |
|---------|---------|----------|-----------|
| 1 | 0 | 1819 | 2228 |
| 1 | 1 | 1784 | 2195 |
| 1 | 2 | 1813 | 2217 |
| 2 | 0 | 2654 | 3415 |
| 2 | 1 | 2638 | 3446 |
| 2 | 2 | 2586 | 3383 |

Thread count has negligible impact. Going from 0→1→2 threads changes RPS by <3%, well within noise. The GIL prevents true parallelism for CPU-bound work, and for I/O-bound FastAPI endpoints the async event loop already handles concurrency within each worker.

Doubling workers from 1→2 gives ~46% more sync RPS and ~54% more async RPS.

### All runners comparison

| Runner | Config | Sync RPS | Async RPS |
|--------|--------|----------|-----------|
| Gunicorn | 1w 0t | 1819 | 2228 |
| Gunicorn | 2w 0t | 2654 | 3415 |
| Uvicorn single-process | — | 1485 | 1760 |
| Uvicorn --workers | 2w | 2203 | 2739 |
| FastAPI CLI | 1w | 1594 | 2039 |
| FastAPI CLI | 2w | 2457 | 3338 |

### Uvicorn multiprocess

| Workers | Sync RPS | Async RPS |
|---------|----------|-----------|
| 1 | 1267 | 1864 |
| 2 | 1850 | 2803 |

## Verdict

> **Individual impact: +50-65% throughput** by switching from Gunicorn w1t0 to FastAPI CLI w2 (or Gunicorn w2t0).

| Config | Best Runner | Sync RPS | Async RPS |
|--------|-------------|----------|-----------|
| 1 worker | Gunicorn 1w0t | 1819 | 2228 |
| 2 workers | Gunicorn 2w0t | 2654 | 3415 |

**Gunicorn wins at both 1w and 2w.** Its process management overhead is negligible and it consistently outperforms all alternatives.

**FastAPI CLI** is the closest competitor — within 12% of Gunicorn at 1w and 6% at 2w.

**Uvicorn single-process** is the slowest — roughly half the throughput of multi-worker setups.

**Uvicorn `--workers`** lags Gunicorn by 17-20% despite being pure ASGI.

**Thread count is irrelevant** — adding threads to Gunicorn changes RPS by less than 3%. Use 0 threads unless you have a specific reason.

**Recommendation**: Use `gunicorn -c gconf.py -k uvicorn.workers.UvicornWorker` for production. FastAPI CLI is a good alternative if you prefer simpler configuration.

Re-run the measurements yourself:
```shell
git clone git@github.com:KissPeter/fastapi-performance-optimization.git
pip3 install -r test_files/requirements.txt
pytest -vv -rP test_files/ -m server_runners
```

## Versions

| Package | Version |
|---------|---------|
| Python | 3.14 |
| FastAPI | 0.139.2 |
| Uvicorn | 0.51.0 |
| Gunicorn | 26.0.0 |
| orjson | 3.11.9 |
| ujson | 5.13.0 |
