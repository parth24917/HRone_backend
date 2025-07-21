from fastapi import FastAPI, HTTPException, Query, Path
from bson import ObjectId
from typing import Optional
import re

from models import ProductCreateModel, OrderCreateModel
from database import product_collection, order_collection

app = FastAPI()

@app.post("/products")
async def create_product(product: ProductCreateModel):
    data = product.dict()
    res = await product_collection.insert_one(data)
    return {"id": str(res.inserted_id)}

@app.get("/products")
async def list_products(
    name: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    query = {}
    if name:
        query["name"] = {"$regex": re.escape(name), "$options": "i"}
    if size:
        query["sizes.size"] = size

    cursor = product_collection.find(query, {"sizes": 0}).sort("_id").skip(offset).limit(limit)
    products = []
    async for p in cursor:
        products.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "price": p["price"]
        })

    return {
        "data": products,
        "page": {
            "next": str(offset + limit),
            "limit": len(products),
            "previous": str(max(offset - limit, 0))
        }
    }

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreateModel):
    order_data = {
        "userId": order.userId,
        "items": [
            {
                "productId": ObjectId(item.productId),
                "qty": item.qty
            } for item in order.items
        ]
    }
    res = await order_collection.insert_one(order_data)
    return {"id": str(res.inserted_id)}

@app.get("/orders/{user_id}")
async def get_orders(user_id: str, limit: int = 10, offset: int = 0):
    pipeline = [
        {"$match": {"userId": user_id}},
        {"$sort": {"_id": 1}},
        {"$skip": offset},
        {"$limit": limit},
        {"$unwind": "$items"},
        {
            "$lookup": {
                "from": "products",
                "localField": "items.productId",
                "foreignField": "_id",
                "as": "productDetails"
            }
        },
        {"$unwind": "$productDetails"},
        {
            "$addFields": {
                "items.productDetails": {
                    "id": {"$toString": "$productDetails._id"},
                    "name": "$productDetails.name",
                    "price": "$productDetails.price"
                }
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "items": {
                    "$push": {
                        "productDetails": "$items.productDetails",
                        "qty": "$items.qty"
                    }
                }
            }
        },
        {
            "$project": {
                "items": 1,
                "total": {
                    "$sum": {
                        "$map": {
                            "input": "$items",
                            "as": "item",
                            "in": {
                                "$multiply": ["$$item.productDetails.price", "$$item.qty"]
                            }
                        }
                    }
                }
            }
        }
    ]

    orders = []
    async for order in order_collection.aggregate(pipeline):
        formatted_items = []
        for i in order["items"]:
            formatted_items.append({
                "productDetails": {
                    "id": i["productDetails"]["id"],
                    "name": i["productDetails"]["name"]
                },
                "qty": i["qty"]
            })
        orders.append({
            "id": str(order["_id"]),
            "items": formatted_items,
            "total": round(order["total"], 2)
        })

    return {
        "data": orders,
        "page": {
            "next": str(offset + limit),
            "limit": len(orders),
            "previous": str(max(offset - limit, 0))
        }
    }
