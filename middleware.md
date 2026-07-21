---
title: Middleware
layout: template
filename: middleware.md
---

# Middleware

FastAPI is based on [Starlette](https://www.starlette.io/) which supports [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/?h=middlew#middleware), a codebase which wraps your application and runs before / after the request processing.
With this you can resolve various functions ( authentication, session, logging, metric collection, etc) without taking care of these functions in your application.
Unfortunately the most straightforward implementation has a drawback, it has major impact on the application latency and throughput. 

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used

## Baseline measurement

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

Sample application without any middleware.
> Note: The test application is available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/app.py) which is from the [FastAPI docs](https://fastapi.tiangolo.com/tutorial/middleware/)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2464.26  |         2671.44  |         2515.29  |      2550.33  |
| Time per request [ms] |           40.58  |           37.433 |           39.757 |        39.2567 |

## FastAPI timing middleware

> Source of middleware is the official [FastAPI docs](https://www.starlette.io/middleware/#basehttpmiddleware)

> You can add middleware as decorator:
```python
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
```

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1618.27  |         1672.64  |         1710.37  |     1667.09   | -34.63 %                 |
| Time per request [ms] |           61.794 |           59.786 |           58.467 |       60.0157 | -20.76 ms                |

### Observations
* Significant drop in the througtput of the container while the average latency raised by ~19ms 

## With two middlewares

Middleware can be defined as child class of [BaseHTTPMiddleware](https://www.starlette.io/middleware/#basehttpmiddleware):
```python
    class CustomHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["Custom"] = "Example"
            return response
```
Alternative way of adding the middleware to the aplication is:
```python
app.add_middleware(CustomHeaderMiddleware)
```

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1231.22  |         1202.6   |         1204.92  |      1212.91  | -52.44 %                 |
| Time per request [ms] |           81.22  |           83.153 |           82.993 |       82.4553 | -43.2 ms                 |

### Observations
* By adding another middleware there is significant drop again, the container throughput is around half than before
* Average response time is raised

## Starlette timing middleware

Fortunately there is a better way of extending the application with middleware capabilities however this is slightly less convenient:
Motivation is from [Starlette Session Middleware](https://github.com/encode/starlette/blob/master/starlette/middleware/sessions.py)

```python
class STARLETTEProcessTimeMiddleware:

    app: ASGIApp

    def __init__(
            self,
            app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start_time = time.time()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Process-Time", str(time.time() - start_time))
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         2491.88  |         2448.96  |         2603.78  |     2514.87   | -1.39 %                  |
| Time per request [ms] |           40.13  |           40.834 |           38.406 |        39.79  | -0.53 ms                 |

### Observations
* Negligible change on performance
* Same function as **FastAPI timing middleware**, but better performance

## With two Starlette middlewares

In order to see the performance difference if multiple middlewares are added, another one has been implemented and measured

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         2482.41  |         2406.58  |         2532.62  |     2473.87   | -3.0 %                   |
| Time per request [ms] |           40.283 |           41.553 |           39.485 |       40.4403 | -1.18 ms                 |

### Observations
* Still no significant difference, much better than BaseHTTPMiddleware 

# Cross-runner middleware overhead

> CI run [29858316413](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29858316413) — Python 3.14, Ubuntu latest.

The same middleware overhead measurement (no middleware baseline vs one FastAPI `@app.middleware("http")` timing middleware) was repeated across all 10 server runner configurations to see whether the overhead varies.

### Sync endpoint (`/sync/items/`)

| Runner | Baseline RPS | +Middleware RPS | Overhead | Baseline Latency | +Middleware Latency | Latency Δ |
|--------|-------------|----------------|----------|------------------|--------------------|-----------|
| Gunicorn w1t0 | 1408.86 | 895.98 | **-36.4%** | 70.99 ms | 111.62 ms | +40.63 ms |
| Gunicorn w2t0 | 2102.94 | 1316.28 | **-37.41%** | 47.58 ms | 75.98 ms | +28.40 ms |
| Gunicorn w1t1 | 1415.21 | 919.91 | **-35.0%** | 70.69 ms | 108.73 ms | +38.04 ms |
| Gunicorn w2t1 | 2111.69 | 1334.62 | **-36.8%** | 47.37 ms | 74.95 ms | +27.59 ms |
| Gunicorn w1t2 | 1392.29 | 879.00 | **-36.87%** | 71.84 ms | 113.78 ms | +41.94 ms |
| Gunicorn w2t2 | 2068.54 | 1294.28 | **-37.43%** | 48.39 ms | 77.28 ms | +28.88 ms |
| Uvicorn single | 1182.71 | 842.83 | **-28.74%** | 84.56 ms | 118.66 ms | +34.10 ms |
| Uvicorn w2 | 1213.57 | 825.69 | **-31.96%** | 82.41 ms | 121.13 ms | +38.72 ms |
| FastAPI CLI w1 | 1428.91 | 916.64 | **-35.85%** | 69.99 ms | 109.10 ms | +39.11 ms |
| FastAPI CLI w2 | 2273.51 | 1460.57 | **-35.76%** | 44.04 ms | 68.57 ms | +24.53 ms |

### Async endpoint (`/async/items/`)

| Runner | Baseline RPS | +Middleware RPS | Overhead | Baseline Latency | +Middleware Latency | Latency Δ |
|--------|-------------|----------------|----------|------------------|--------------------|-----------|
| Gunicorn w1t0 | 1705.74 | 1045.71 | **-38.69%** | 58.74 ms | 95.66 ms | +36.93 ms |
| Gunicorn w2t0 | 2664.84 | 1606.84 | **-39.70%** | 37.53 ms | 62.25 ms | +24.72 ms |
| Gunicorn w1t1 | 1734.10 | 1041.17 | **-39.96%** | 57.67 ms | 96.10 ms | +38.43 ms |
| Gunicorn w2t1 | 2659.98 | 1648.26 | **-38.03%** | 37.62 ms | 60.68 ms | +23.06 ms |
| Gunicorn w1t2 | 1721.13 | 1034.53 | **-39.89%** | 58.10 ms | 96.68 ms | +38.58 ms |
| Gunicorn w2t2 | 2682.76 | 1573.81 | **-41.34%** | 37.29 ms | 63.57 ms | +26.29 ms |
| Uvicorn single | 1451.85 | 958.20 | **-34.0%** | 68.89 ms | 104.38 ms | +35.49 ms |
| Uvicorn w2 | 1480.07 | 982.76 | **-33.6%** | 67.57 ms | 101.76 ms | +34.19 ms |
| FastAPI CLI w1 | 1841.48 | 1061.92 | **-42.33%** | 54.31 ms | 94.17 ms | +39.86 ms |
| FastAPI CLI w2 | 3034.90 | 1701.06 | **-43.95%** | 32.95 ms | 58.79 ms | +25.84 ms |

### Observations
* **Middleware overhead is consistent across runners**: ~35-44% throughput drop regardless of server configuration
* **Uvicorn shows slightly lower overhead** (~29-34%) compared to Gunicorn and FastAPI CLI (~35-44%)
* The absolute latency increase is 24-42 ms across all runners
* Adding more workers/threads does not mitigate the middleware overhead — it's a per-request cost

# Verdict
Numbers clearly indicate the **significant performance improvement** between BaseHTTPMiddleware and Starlette middleware. Avoid using BaseHTTPMiddleware if you can. The overhead is **consistent across all server runners** — no runner configuration can compensate for the middleware cost.