from pydantic import BaseModel, Field
from typing import List

class SizeModel(BaseModel):
    size: str
    quantity: int

class ProductCreateModel(BaseModel):
    name: str
    price: float
    sizes: List[SizeModel]

class OrderItemModel(BaseModel):
    productId: str
    qty: int

class OrderCreateModel(BaseModel):
    userId: str
    items: List[OrderItemModel]
