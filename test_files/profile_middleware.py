"""
Profile app_files/app.py with cProfile under three configurations:
baseline (no middleware), BaseHTTPMiddleware, and plain Starlette ASGI middleware.

The app's ASGI callable is invoked directly (no TestClient/httpx in the loop) so the
profile isolates middleware overhead from HTTP client overhead.

Usage:
    MODE=baseline  python3 test_files/profile_middleware.py
    MODE=base_http python3 test_files/profile_middleware.py
    MODE=starlette python3 test_files/profile_middleware.py
"""
import asyncio
import cProfile
import json
import os
import pstats
import sys

MODE = os.environ.get("MODE", "baseline")
N = int(os.environ.get("N", "2000"))
SORT = os.environ.get("SORT", "tottime")
PSTATS_OUT = os.environ.get("PSTATS_OUT")
if PSTATS_OUT:
    PSTATS_OUT = os.path.abspath(PSTATS_OUT)

APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app_files")
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

if MODE == "base_http":
    os.environ["CUSTOMHEADERMIDDLEWARE"] = "1"
elif MODE == "starlette":
    os.environ["STARLETTECUSTOMHEADERMIDDLEWARE"] = "1"
elif MODE != "baseline":
    raise SystemExit(f"unknown MODE {MODE!r}, expected baseline|base_http|starlette")

import app as app_module  # noqa: E402

asgi_app = app_module.app
body = json.dumps({"name": "Foo", "price": 1.0}).encode()


def make_scope():
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/sync/items/",
        "raw_path": b"/sync/items/",
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
        "server": ("testserver", 80),
        "client": ("testclient", 123),
        "scheme": "http",
    }


async def run_one():
    scope = make_scope()
    sent = {"done": False}

    async def receive():
        if not sent["done"]:
            sent["done"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    messages = []

    async def send(message):
        messages.append(message)

    await asgi_app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    assert status == 200, messages


async def run_many(n):
    for _ in range(n):
        await run_one()


async def main():
    await run_many(50)  # warm-up: skip first-call import/cache costs

    profiler = cProfile.Profile()
    profiler.enable()
    await run_many(N)
    profiler.disable()
    return profiler


profiler = asyncio.run(main())

stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats(SORT).print_stats(25)

if PSTATS_OUT:
    pstats.Stats(profiler).strip_dirs().dump_stats(PSTATS_OUT)
