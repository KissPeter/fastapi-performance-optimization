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

Sample application without any middleware.
> Note: The test application is available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/app.py) which is from the [FastAPI docs](https://fastapi.tiangolo.com/tutorial/middleware/)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1358.26  |         1522.84  |          1529.98 |      1470.36  |
| Time per request [ms] |           73.624 |           65.667 |            65.36 |        68.217 |


## With one middleware

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
| Requests per second   |         1082.77  |         1096.65  |         1102.55  |     1093.99   | -25.6 %                  |
| Time per request [ms] |           92.355 |           91.187 |           90.699 |       91.4137 | -23.2 ms                 |


### Observations
* Significant drop in the througtput of the container while the average latency raised by ~23ms 

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
| Requests per second   |          887.37  |           864.75 |          880.64  |       877.587 | -40.31 %                 |
| Time per request [ms] |          112.693 |           115.64 |          113.554 |       113.962 | -45.75 ms                |

### Observations
* By adding another middleware there is significant drop again, the container throughput is around half than before
* Average response time is raised

## With one Starlette middleware

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
| Requests per second   |         1490.14  |         1498.82  |         1489.44  |     1492.8    | 1.53 %                   |
| Time per request [ms] |           67.108 |           66.719 |           67.139 |       66.9887 | 1.23 ms                  |

### Observations
* Negligible change on performance 

## With two Starlette middlewares

In order to see the performance difference if multiple middlewares are added, another one has been implemented and measured

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1466.56  |         1499.56  |         1461.85  |       1475.99 | 0.38 %                   |
| Time per request [ms] |           68.187 |           66.686 |           68.407 |         67.76 | 0.46 ms                  |

### Observations
* Still no significant difference, much better than BaseHTTPMiddleware 
