---
title: FastAPI performance optimisation
layout: template
filename: index.md
---

# FastAPI performance tuning

[FastAPI](https://fastapi.tiangolo.com/) is a great, high performance web framework but far from perfect.
This document is intended to provide some tips and ideas to get the most out of it


# Use these techniques to achieve 100-300% performance increase from your FastAPI application

> All tested on the same sized Docker containers (2 CPU cores). The performance numbers below represent real CI-verified measurements.

## Combined optimization impact

Each optimization below has a measurable, compounding effect. When applied together, the total improvement is multiplicative, not additive.

| Optimization | Individual Impact | CI-verified |
|-------------|-------------------|-------------|
| **Sync → Async endpoints** | +20-33% throughput | [Details](https://kisspeter.github.io/fastapi-performance-optimization/sync_vs_async) |
| **JSON → ORJSON response class** | +4-13% throughput | [Details](https://kisspeter.github.io/fastapi-performance-optimization/json_response_class) |
| **BaseHTTPMiddleware → Starlette ASGI middleware** | +35-44% throughput (avoiding BaseHTTPMiddleware cost) | [Details](https://kisspeter.github.io/fastapi-performance-optimization/middleware) |
| **Gunicorn w1t0 → FastAPI CLI w2** | +50-65% throughput (proper worker scaling) | [Details](https://kisspeter.github.io/fastapi-performance-optimization/server_runners) |
| **Nginx TCP port → Unix socket** | +150-276% throughput (nginx-to-app communication) | [Details](https://kisspeter.github.io/fastapi-performance-optimization/nginx_port_socket) |
| **Best vs Worst combo (CI verified)** | **+100-297% throughput** | [Details](#measured-best-vs-worst-configurations) |

## Measured best vs worst configurations

> CI run [30018301964](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/30018301964) — all 4 jobs passed.

Using the big JSON response endpoint (1MB payload) across all tested combinations:

### Sync endpoint (`/sync/big_json_response`)

| Configuration | RPS | Latency |
|--------------|-----|---------|
| **Best**: FastAPI CLI w2 + async + ORJSON + Starlette ASGI | 3405 | 29.4 ms |
| **Worst**: Gunicorn w1t0 + sync + JSON + BaseHTTPMiddleware | 1695 | 59.1 ms |
| **Improvement** | **+100.85%** | **-29.7 ms** |

### Async endpoint (`/async/big_json_response`)

| Configuration | RPS | Latency |
|--------------|-----|---------|
| **Best**: FastAPI CLI w2 + async + ORJSON + Starlette ASGI | 3433 | 29.4 ms |
| **Worst**: Gunicorn w1t0 + sync + JSON + BaseHTTPMiddleware | 864 | 180.1 ms |
| **Improvement** | **+297%** | **-150.7 ms** |

### Small payload endpoints

| Endpoint | Best RPS | Worst RPS | Improvement |
|----------|----------|-----------|-------------|
| `/sync/items/` | 2081 | 974 | **+113.6%** |
| `/async/items/` | 2656 | 867 | **+206.4%** |

### The compounding effect

When you combine ALL optimizations:

| Factor | Worst config | Best config |
|--------|-------------|-------------|
| Server runner | Gunicorn w1t0 | FastAPI CLI w2 |
| Endpoint type | Sync | Async |
| Response class | JSON | ORJSON |
| Middleware | BaseHTTPMiddleware | Starlette ASGI (or none) |
| Nginx transport | TCP port | Unix socket |
| **Combined RPS (big JSON)** | **864** | **3433** |
| **Combined improvement** | | **~4x throughput** |

> The difference between a default FastAPI setup and a properly optimized one is **4x throughput** on big JSON responses and **3x on small payloads**. These are not theoretical numbers — they are measured in CI on identical Docker infrastructure (2 CPU cores per container).

## All optimization topics

## [Fastapi Middleware performance tuning](https://kisspeter.github.io/fastapi-performance-optimization/middleware)
## [Fastapi JSON response classes comparison](https://kisspeter.github.io/fastapi-performance-optimization/json_response_class)
## [Gunicorn workers and threads](https://kisspeter.github.io/fastapi-performance-optimization/workers_and_threads)
## [Nginx in front of FastAPI](https://kisspeter.github.io/fastapi-performance-optimization/nginx_port_socket)
## [Connection keepalive](https://kisspeter.github.io/fastapi-performance-optimization/keepalive)
## [Server Runners: Gunicorn vs Uvicorn vs FastAPI CLI](https://kisspeter.github.io/fastapi-performance-optimization/server_runners)
## [Sync / Async API Endpoints](https://kisspeter.github.io/fastapi-performance-optimization/sync_vs_async)
## [Connection Pool Size of External Resources](https://kisspeter.github.io/fastapi-performance-optimization/connection_pool)
## [Thread Pool Sizing (anyio tokens)](https://kisspeter.github.io/fastapi-performance-optimization/thread_pool_sizing)
## [Per-Worker Connection Pool](https://kisspeter.github.io/fastapi-performance-optimization/per_worker_connection_pool)
## [Pool Sizing Calculator](https://kisspeter.github.io/fastapi-performance-optimization/pool_sizing_calculator)

# Robustness & Reliability (Generic, not FastAPI-specific)

These patterns apply to any Python web application. They contribute to a robust and reliable application but are not FastAPI performance optimizations.

## [Retry Patterns and Circuit Breaker](https://kisspeter.github.io/fastapi-performance-optimization/retry_circuit_breaker)

# Stay tuned for new ideas:
## FastAPI application profiling
### Arbitrary place of code
### Profiling middleware

### Test environment
* All the tests were run on  [GitHub Actions](https://github.com/KissPeter/fastapi-performance-optimization/actions/workflows/performance_tuning_measurements.yml)
* Application is built into a container, you can build it like this:
```shell
docker-compose build
```
* The container has two CPU cores allocated in order to preserve resource for the test client:
```Dockerfile
  app:
    container_name: fastapi-performance-optimization
    build:
      context: app_files
      dockerfile: Dockerfile
    image: fastapi-performance-optimization:latest
    cpus: 2
    restart: always
```
* All the tests were run with the same [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) tool configuration available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/compare_container_performance.py#L51)
    * ab config: `ab -q -c 100 -n 1000 -T 'application/json' ...`
* All tests were run 3 times and average has been calculated
* Before test run the container has been pre-warmed with small amount of queries, result didn't count in the measurement
* Versions used for these measurements is in the [Dockerfile](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/Dockerfile)
* Interested in re-running the tests in your environment?
```shell
  git clone git@github.com:KissPeter/fastapi-performance-optimization.git
  pip3 install -r test_files/requirements.txt 
  pytest -vv -rP test_files/
```
