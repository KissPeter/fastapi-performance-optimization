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

# Verdict
Numbers clearly indicate the **significant performance improvement** between BaseHTTPMiddleware and Starlette middleware. Avoid using BaseHTTPMiddleware if you can