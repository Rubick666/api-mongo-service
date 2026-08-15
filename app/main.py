from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.product import Product
from app.routers import product

app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB-backed product catalog service",
)

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product],
    )
    # Create text indexes for future full‑text search
    await Product.create_indexes()
    print("Connected to MongoDB and Beanie initialized.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}

# Include the products router
app.include_router(product.router, prefix="/products", tags=["products"])