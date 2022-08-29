---
title: Middleware
layout: template
filename: middleware.md
---

# Middleware

FastAPI is based on [Starlette](https://www.starlette.io/) which supports [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/?h=middlew#middleware), a codebase which wraps your application and runs before / after the request processing.
With this you can resolve various functions ( authentication, session, logging, metric collection, etc) without taking care of these functions in your application.
Unfortunately the most straightforward implementation has a drawback, it has major impact on the application latency and throughput. 

### Test environment
* All the tests were run on a machine with i5-2520M CPU
* Application is built into a container:
```shell
docker build -f Dockerfile -t fastapi_test:latest .
```
* The container has two CPU cores allocated in order to preserve resource for the test client:
```shell
docker run -p 127.0.0.1:8000:8000 --cpus=2 -it fastapi_test:latest
```
* All the tests were run with the same [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) tool configuration available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/run_ab.sh)
* Before test run the container has been pre-warmed

### Baseline measurement

Sample application without any middleware.
> Note: The test application is available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/app.py) which is from the [FastAPI docs](https://fastapi.tiangolo.com/tutorial/middleware/)

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|-----------------------|----------------|----------------|----------------|-------------|
| Requests per second   | 1013,27        | 1059,05        | 1036,21        | **1036,18** |
| Time per request [ms] | 98,69          | 94,42          | 96,51          | **96,54**   |


### With one middleware

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

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|-----------------------|----------------|----------------|----------------|-------------|----------------------------|
| Requests per second   | 686,21         | 689,44         | 674,9          | **683,52**  | -51,59                     |
| Time per request [ms] | 145,728        | 145,044        | 148,17         | **146,31**  | 34,03                      |

#### Observations
* Significant drop in the througtput of the container while the average latency raised by ~34ms 

### With two middlewares

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

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|-----------------------|----------------|----------------|----------------|-------------|----------------------------|
| Requests per second   | 481,74         | 495,27         | 485,43         | **487,48**  | -112,56                    |
| Time per request [ms] | 207,58         | 201,91         | 206,005        | **205,17**  | 52,95                      |

#### Observations
* By adding another middleware there is significant drop again, the container throughtput is less than half than before
* Average response time is doupled

### With one Starlette middleware

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

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|-----------------------|----------------|----------------|----------------|-------------|----------------------------|
| Requests per second   | 1078,18        | 1069,59        | 971,28         | **1039,68** | 0,34                       |
| Time per request [ms] | 92,75          | 93,49          | 102,96         | **96,40**   | -0,15                      |

#### Observations
* Negligable change on performance 

### With two Starlette middlewares

In order to see the performance difference if multiple middlewares are added, another one has been implemented and measured

| **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|-----------------------|----------------|----------------|----------------|-------------|----------------------------|
| Requests per second   | 878,93	        | 941,79	        | 975,64	        | **932,12**  | 	-11,16                    |
| Time per request [ms] | 113,77         | 	106,18	       | 102,6          | **107,52**  | 	10,21                     |

#### Observations
* Some performance drop but less significant as for BaseHTTPMiddleware
