import os
import time
import threading
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from fastapi.responses import ORJSONResponse, UJSONResponse, JSONResponse
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# from https://fastapi.tiangolo.com/tutorial/body/#import-pydantics-basemodel
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


resp_class = os.getenv("JSONRESPONSECLASS", "JSONResponse")
resp_classes = {
    "ORJSONResponse": ORJSONResponse,
    "UJSONResponse": UJSONResponse,
    "JSONResponse": JSONResponse
}
if resp_class in ["ORJSONResponse", "UJSONResponse", "JSONResponse"]:
    print(f"Set {resp_class}")
else:
    print(f"Unsupported response class: {resp_class}, falling back to JSONResponse")
    resp_class = "JSONResponse"

app = FastAPI(debug=False, default_response_class=resp_classes.get(resp_class))
json_data = json.load(open('./test_json_1MB.json'))


@app.post("/async/items/")
async def create_item(item: Item):
    return item


@app.post("/sync/items/")
def create_item(item: Item):
    return item


@app.post("/async/big_json_response/")
async def big_json_response(item: Item):
    _ = item
    return json_data


@app.post("/sync/big_json_response/")
def big_json_response(item: Item):
    _ = item
    return json_data


# from https://fastapi.tiangolo.com/tutorial/middleware/

if os.getenv("PROCESSTIMEMIDDLEWARE"):
    print("Load PROCESSTIMEMIDDLEWARE")


    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

# from https://www.starlette.io/middleware/#basehttpmiddleware

if os.getenv("CUSTOMHEADERMIDDLEWARE"):
    print("Load CUSTOMHEADERMIDDLEWARE")


    class CustomHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["Custom"] = "Example"
            return response


    app.add_middleware(CustomHeaderMiddleware)


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


if os.getenv("STARLETTEPROCESSTIMEIDDLEWARE"):
    print("Load STARLETTEPROCESSTIMEIDDLEWARE")

    app.add_middleware(STARLETTEProcessTimeMiddleware)


class STARLETTECustomHeaderMiddleware:
    """Load request ID from headers if present. Generate one otherwise."""

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

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("Custom", "Example")
            await send(message)

        await self.app(scope, receive, send_wrapper)


if os.getenv("STARLETTECUSTOMHEADERMIDDLEWARE"):
    print("Load STARLETTECUSTOMHEADERMIDDLEWARE")

    app.add_middleware(STARLETTECustomHeaderMiddleware)


EXTERNAL_API_HOST = os.getenv("EXTERNAL_API_HOST", "http://mock-api:8030")
CONN_POOL_LIMIT = int(os.getenv("CONN_POOL_LIMIT", "100"))
CONN_POOL_KEEPALIVE = int(os.getenv("CONN_POOL_KEEPALIVE", "20"))
CONN_POOL_TIMEOUT = int(os.getenv("CONN_POOL_TIMEOUT", "60"))

ANYIO_TOKENS = int(os.getenv("ANYIO_TOKENS", "0"))
if ANYIO_TOKENS > 0:
    import anyio.to_thread
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = ANYIO_TOKENS
    print(f"Set anyio thread pool tokens to {ANYIO_TOKENS}")

if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
    print(f"Loading connection pool endpoints (target: {EXTERNAL_API_HOST}, "
          f"pool_limit: {CONN_POOL_LIMIT}, pool_keepalive: {CONN_POOL_KEEPALIVE})")

    _sync_client = httpx.Client(
        base_url=EXTERNAL_API_HOST,
        limits=httpx.Limits(
            max_connections=CONN_POOL_LIMIT,
            max_keepalive_connections=CONN_POOL_KEEPALIVE,
        ),
        timeout=httpx.Timeout(CONN_POOL_TIMEOUT),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with httpx.AsyncClient(
            base_url=EXTERNAL_API_HOST,
            limits=httpx.Limits(
                max_connections=CONN_POOL_LIMIT,
                max_keepalive_connections=CONN_POOL_KEEPALIVE,
            ),
            timeout=httpx.Timeout(CONN_POOL_TIMEOUT),
        ) as client:
            application.state.async_client = client
            yield

    app.router.lifespan_context = lifespan

    @app.post("/sync_pool/items/")
    def sync_pool_item(item: Item):
        response = _sync_client.post("/mock/items/", json=item.model_dump())
        return response.json()

    @app.post("/async_pool/items/")
    async def async_pool_item(item: Item):
        response = await app.state.async_client.post(
            "/mock/items/", json=item.model_dump()
        )
        return response.json()


# === Concurrency introspection endpoints ===
import os as _os
import threading as _threading

_concurrency_counter = _threading.Lock()
_concurrent_requests = {"count": 0}
_concurrent_lock = _threading.Lock()


def _increment_concurrent():
    with _concurrent_lock:
        _concurrent_requests["count"] += 1
        return _concurrent_requests["count"]


def _decrement_concurrent():
    with _concurrent_lock:
        _concurrent_requests["count"] -= 1


@app.get("/info/worker")
def worker_info():
    """Report worker identity and current concurrency."""
    return {
        "worker_pid": _os.getpid(),
        "thread_id": _threading.current_thread().ident,
        "thread_name": _threading.current_thread().name,
        "concurrent_requests": _concurrent_requests["count"],
    }


@app.get("/info/slow_sync")
def slow_sync_info(delay: float = 0.5):
    """Sync endpoint that tracks concurrency while calling external API.
    This proves how many sync threads are active simultaneously."""
    count = _increment_concurrent()
    try:
        if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
            response = _sync_client.post(
                "/mock/slow/items/",
                json={"name": "test", "price": 1.0},
                params={"delay": delay},
            )
            result = response.json()
        else:
            time.sleep(delay)
            result = {"delayed": delay}
        return {
            "worker_pid": _os.getpid(),
            "thread_id": _threading.current_thread().ident,
            "concurrent_at_start": count,
            "concurrent_at_end": _concurrent_requests["count"],
            "result": result,
        }
    finally:
        _decrement_concurrent()


@app.get("/info/slow_async")
async def slow_async_info(delay: float = 0.5):
    """Async endpoint that tracks concurrency while calling external API."""
    count = _increment_concurrent()
    try:
        if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
            response = await app.state.async_client.post(
                "/mock/slow/items/",
                json={"name": "test", "price": 1.0},
                params={"delay": delay},
            )
            result = response.json()
        else:
            import asyncio
            await asyncio.sleep(delay)
            result = {"delayed": delay}
        return {
            "worker_pid": _os.getpid(),
            "thread_id": _threading.current_thread().ident,
            "concurrent_at_start": count,
            "concurrent_at_end": _concurrent_requests["count"],
            "result": result,
        }
    finally:
        _decrement_concurrent()


# === Pool exhaustion / timeout endpoint ===

@app.get("/info/slow_sync_timeout")
def slow_sync_timeout_info(delay: float = 0.5):
    """Sync endpoint that demonstrates pool exhaustion behavior.
    When pool is small and requests exceed pool_size, handlers queue.
    If they queue longer than httpx timeout, the request fails."""
    count = _increment_concurrent()
    try:
        if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
            try:
                response = _sync_client.post(
                    "/mock/slow/items/",
                    json={"name": "test", "price": 1.0},
                    params={"delay": delay},
                )
                result = response.json()
                status = "ok"
            except httpx.TimeoutException:
                result = {"error": "timeout"}
                status = "timeout"
            except httpx.ConnectError as e:
                result = {"error": f"connect_error: {e}"}
                status = "connect_error"
        else:
            time.sleep(delay)
            result = {"delayed": delay}
            status = "ok"
        return {
            "worker_pid": _os.getpid(),
            "concurrent_at_start": count,
            "status": status,
            "result": result,
        }
    finally:
        _decrement_concurrent()


# === Retry pattern ===

import random as _random

@app.get("/info/retry_sync")
def retry_sync_info(
    delay: float = 0.1,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
):
    """Sync endpoint with retry + exponential backoff.
    Demonstrates retry pattern for transient failures."""
    count = _increment_concurrent()
    attempts = 0
    last_error = None
    try:
        for attempt in range(max_retries + 1):
            attempts += 1
            if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
                try:
                    response = _sync_client.post(
                        "/mock/flaky/items/",
                        json={"name": "test", "price": 1.0},
                        params={"delay": delay, "fail_rate": "0.3"},
                    )
                    result = response.json()
                    return {
                        "worker_pid": _os.getpid(),
                        "concurrent_at_start": count,
                        "attempts": attempts,
                        "status": "ok",
                        "result": result,
                    }
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    last_error = str(e)
                    if attempt < max_retries:
                        wait = backoff_factor * (2 ** attempt)
                        time.sleep(wait)
            else:
                if _random.random() < 0.3:
                    last_error = "simulated failure"
                    if attempt < max_retries:
                        wait = backoff_factor * (2 ** attempt)
                        time.sleep(wait)
                else:
                    return {
                        "worker_pid": _os.getpid(),
                        "concurrent_at_start": count,
                        "attempts": attempts,
                        "status": "ok",
                        "result": {"delayed": delay},
                    }
        return {
            "worker_pid": _os.getpid(),
            "concurrent_at_start": count,
            "attempts": attempts,
            "status": "exhausted",
            "error": last_error,
        }
    finally:
        _decrement_concurrent()


# === Circuit breaker ===

_cb_state = {"failures": 0, "state": "closed", "last_failure": 0.0}
_cb_lock = _threading.Lock()
CB_FAILURE_THRESHOLD = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
CB_RECOVERY_TIMEOUT = float(os.getenv("CB_RECOVERY_TIMEOUT", "10.0"))


def _cb_record_success():
    with _cb_lock:
        _cb_state["failures"] = 0
        _cb_state["state"] = "closed"


def _cb_record_failure():
    with _cb_lock:
        _cb_state["failures"] += 1
        _cb_state["last_failure"] = time.time()
        if _cb_state["failures"] >= CB_FAILURE_THRESHOLD:
            _cb_state["state"] = "open"


def _cb_should_allow():
    with _cb_lock:
        if _cb_state["state"] == "closed":
            return True
        if _cb_state["state"] == "open":
            if time.time() - _cb_state["last_failure"] > CB_RECOVERY_TIMEOUT:
                _cb_state["state"] = "half-open"
                return True
            return False
        return True


@app.get("/info/circuit_breaker_sync")
def circuit_breaker_sync_info(delay: float = 0.1):
    """Sync endpoint with circuit breaker pattern.
    Stops calling external service after N consecutive failures."""
    count = _increment_concurrent()
    try:
        if not _cb_should_allow():
            return {
                "worker_pid": _os.getpid(),
                "concurrent_at_start": count,
                "status": "circuit_open",
                "circuit_state": _cb_state["state"],
                "failures": _cb_state["failures"],
            }

        if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
            try:
                response = _sync_client.post(
                    "/mock/flaky/items/",
                    json={"name": "test", "price": 1.0},
                    params={"delay": delay, "fail_rate": "0.5"},
                )
                result = response.json()
                _cb_record_success()
                return {
                    "worker_pid": _os.getpid(),
                    "concurrent_at_start": count,
                    "status": "ok",
                    "circuit_state": _cb_state["state"],
                    "failures": _cb_state["failures"],
                    "result": result,
                }
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                _cb_record_failure()
                return {
                    "worker_pid": _os.getpid(),
                    "concurrent_at_start": count,
                    "status": "error",
                    "circuit_state": _cb_state["state"],
                    "failures": _cb_state["failures"],
                    "error": str(e),
                }
        else:
            if _random.random() < 0.5:
                _cb_record_failure()
                return {
                    "worker_pid": _os.getpid(),
                    "concurrent_at_start": count,
                    "status": "error",
                    "circuit_state": _cb_state["state"],
                    "failures": _cb_state["failures"],
                    "error": "simulated failure",
                }
            else:
                _cb_record_success()
                return {
                    "worker_pid": _os.getpid(),
                    "concurrent_at_start": count,
                    "status": "ok",
                    "circuit_state": _cb_state["state"],
                    "failures": _cb_state["failures"],
                    "result": {"delayed": delay},
                }
    finally:
        _decrement_concurrent()
