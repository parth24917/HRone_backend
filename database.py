from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["ecommerce"]
product_collection = db["products"]
order_collection = db["orders"]
