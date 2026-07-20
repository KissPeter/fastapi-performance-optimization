from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

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


@app.get("/mock/health")
def health():
    return {"status": "ok"}
