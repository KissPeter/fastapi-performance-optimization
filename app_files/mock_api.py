from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import time

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


@app.get("/mock/health")
def health():
    return {"status": "ok"}
