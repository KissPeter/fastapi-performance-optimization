---
title: Server Runners Comparison
layout: template
filename: server_runners.md
---


# Server Runners Comparison

This benchmark compares five ways to run a FastAPI application in production:
- **Gunicorn** with UvicornWorker — WSGI process manager spawning Uvicorn workers (tested with 0 and 1 threads)
- **Uvicorn** — single-process ASGI server (no `--workers`)
- **Uvicorn with `--workers`** — ASGI server with native multi-process mode
- **FastAPI CLI** (`fastapi run --workers`) — official FastAPI CLI wrapping Uvicorn with `--workers`
- **Uvicorn multiprocess** — Uvicorn spawned via multiprocessing (separate from `--workers`)

All runners use the same underlying ASGI server (Uvicorn). The difference is in how they manage processes and handle startup.

## Server Runners

### Gunicorn with UvicornWorker
[Gunicorn](https://gunicorn.org/) is a mature WSGI HTTP server that runs ASGI applications via the [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) class. It acts as a process manager, spawning multiple Uvicorn worker processes. This has been the recommended production setup for FastAPI.

### Uvicorn (single process)
[Uvicorn](https://www.uvicorn.org/) is a lightning-fast ASGI server. Running it without `--workers` uses a single process. Gunicorn's documentation [suggests](https://www.uvicorn.org/deployment/#gunicorn) running behind Gunicorn for production.

### Uvicorn with `--workers`
Uvicorn natively supports the `--workers` flag to spawn multiple worker processes. Each worker is a standalone Uvicorn process. This is simpler than Gunicorn but lacks its process management features (graceful restarts, worker recycling, etc.).

### FastAPI CLI
[FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/) (`fastapi run --workers N`) is the official way to run FastAPI apps. Under the hood, it uses Uvicorn with `--workers`. This is the simplest way to get multi-process FastAPI running.

## Measurements

> CI run [29812055044](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29812055044) — Python 3.14, Ubuntu latest.

### All runners, 2 workers — Sync endpoint

Gunicorn w2t0 used as baseline.

| Runner | Config | RPS | vs Gunicorn |
|--------|--------|-----|-------------|
| Gunicorn | 2w 0t (baseline) | 2242 | — |
| Gunicorn | 2w 1t | 2204 | -1.71 % |
| Uvicorn | 2w | 1265 | -43.56 % |
| Uvicorn --workers | 2w | 1842 | -17.86 % |
| FastAPI CLI | 2w | 2332 | +4.03 % |

### All runners, 2 workers — Async endpoint

| Runner | Config | RPS | vs Gunicorn |
|--------|--------|-----|-------------|
| Gunicorn | 2w 0t (baseline) | 3536 | — |
| Gunicorn | 2w 1t | 3577 | +1.15 % |
| Uvicorn | 2w | 1876 | -46.93 % |
| Uvicorn --workers | 2w | 2808 | -20.58 % |
| FastAPI CLI | 2w | 3891 | +10.05 % |

### Gunicorn thread impact — Sync endpoint

Gunicorn w2t0 used as baseline.

| Runner | Config | RPS | vs w2t0 |
|--------|--------|-----|---------|
| Gunicorn | 2w 0t (baseline) | 2231 | — |
| Gunicorn | 1w 0t | 1466 | -34.28 % |
| Gunicorn | 1w 1t | 1442 | -35.36 % |
| Gunicorn | 2w 1t | 2218 | -0.58 % |

### Gunicorn thread impact — Async endpoint

| Runner | Config | RPS | vs w2t0 |
|--------|--------|-----|---------|
| Gunicorn | 2w 0t (baseline) | 3560 | — |
| Gunicorn | 1w 0t | 2315 | -34.98 % |
| Gunicorn | 1w 1t | 2312 | -35.06 % |
| Gunicorn | 2w 1t | 3593 | +0.91 % |

### Uvicorn multiprocess

| Runner | Config | Sync RPS | Async RPS |
|--------|--------|----------|-----------|
| Uvicorn multiprocess | 1w | 1267 | 1864 |
| Uvicorn multiprocess | 2w | 1850 | 2803 |

## Summary matrix

| Runner | Config | Sync RPS | Async RPS |
|--------|--------|----------|-----------|
| Gunicorn | 2w 0t | 2242 | 3536 |
| Gunicorn | 2w 1t | 2204 | 3577 |
| Gunicorn | 1w 0t | 1466 | 2315 |
| Gunicorn | 1w 1t | 1442 | 2312 |
| Uvicorn single-process | 2w | 1265 | 1876 |
| Uvicorn --workers | 2w | 1842 | 2808 |
| FastAPI CLI | 2w | 2332 | 3891 |
| Uvicorn multiprocess | 1w | 1267 | 1864 |
| Uvicorn multiprocess | 2w | 1850 | 2803 |

## Verdict

| Workers | Best Runner | RPS (sync/async) | vs Gunicorn |
|---------|-------------|-------------------|-------------|
| 2 workers | FastAPI CLI | 2332 / 3891 | +4-10 % |

**FastAPI CLI wins across the board.** With 2 workers it outperforms Gunicorn by 4% (sync) to 10% (async). Both use Uvicorn under the hood, but FastAPI CLI's startup path is more efficient.

**Gunicorn with 0 vs 1 thread:** Thread count makes virtually no difference. Adding1 thread to 2 workers changes RPS by less than 2%, well within noise. The GIL prevents true parallelism for CPU-bound work, and for I/O-bound FastAPI endpoints the async event loop already handles concurrency within each worker.

**Gunicorn 1w vs 2w:** Doubling workers from1→2 gives ~53% more sync RPS and ~53% more async RPS. Near-linear scaling.

**Uvicorn single-process** is the slowest — roughly half the throughput of Gunicorn or FastAPI CLI with 2 workers. Single-process ASGI cannot utilize multiple CPU cores.

**Uvicorn `--workers`** lags behind Gunicorn by 18-21%. Despite being pure ASGI without the WSGI bridge, its process management is less efficient than Gunicorn's.

**Uvicorn multiprocess** performs similarly to Uvicorn `--workers` — expected since both spawn multiple Uvicorn processes.

**Recommendation**: Use `fastapi run --workers N` for multi-worker deployments. Use Gunicorn with UvicornWorker when you need its operational features (graceful restarts, worker recycling, resource limits).

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
