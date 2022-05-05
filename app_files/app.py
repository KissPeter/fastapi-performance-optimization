import os
import time
from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# from https://fastapi.tiangolo.com/tutorial/body/#import-pydantics-basemodel
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item):
    return item


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
