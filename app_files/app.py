import os
import time
import threading
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

if HTTPX_AVAILABLE and EXTERNAL_API_HOST:
    print(f"Loading connection pool endpoints (target: {EXTERNAL_API_HOST}, "
          f"pool_limit: {CONN_POOL_LIMIT}, pool_keepalive: {CONN_POOL_KEEPALIVE})")

    _sync_client = httpx.Client(
        base_url=EXTERNAL_API_HOST,
        limits=httpx.Limits(
            max_connections=CONN_POOL_LIMIT,
            max_keepalive_connections=CONN_POOL_KEEPALIVE,
        ),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with httpx.AsyncClient(
            base_url=EXTERNAL_API_HOST,
            limits=httpx.Limits(
                max_connections=CONN_POOL_LIMIT,
                max_keepalive_connections=CONN_POOL_KEEPALIVE,
            ),
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
