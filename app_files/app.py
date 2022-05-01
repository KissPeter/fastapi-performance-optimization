from typing import Optional

from pydantic import BaseModel
import time
import os
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


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

if os.getenv("MIDDLEWARE"):
    print("Load MIDDLEWARE")


    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

# from https://www.starlette.io/middleware/#basehttpmiddleware

if os.getenv("DUMMYMIDDLEWARE"):
    print("Load DummyMiddleware")


    class DummyMiddleware(BaseHTTPMiddleware):

        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["Custom"] = "Example"
            return response

    app.add_middleware(DummyMiddleware)