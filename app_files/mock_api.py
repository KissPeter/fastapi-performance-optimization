from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import time
import random

app = FastAPI()


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


MOCK_RESPONSE = {
    "id": 1,
    "name": "mock_item",
    "description": "A mock item for connection pool testing",
    "price": 9.99,
    "tax": 1.5,
    "category": "test",
    "in_stock": True,
}


@app.post("/mock/items/")
def mock_item(item: Item):
    return MOCK_RESPONSE


@app.post("/mock/slow/items/")
def mock_slow_item(item: Item, delay: float = Query(default=0.5)):
    """Simulate slow external API. delay in seconds."""
    time.sleep(delay)
    return MOCK_RESPONSE


@app.post("/mock/flaky/items/")
def mock_flaky_item(
    item: Item,
    delay: float = Query(default=0.1),
    fail_rate: float = Query(default=0.3),
):
    """Simulate flaky external API. Fails randomly with given fail_rate."""
    time.sleep(delay)
    if random.random() < fail_rate:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"error": "service_unavailable", "mock": True},
        )
    return MOCK_RESPONSE


@app.get("/mock/health")
def health():
    return {"status": "ok"}
