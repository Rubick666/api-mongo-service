from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.product import Product  # will be imported later
from app.routers import products

app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB-backed product catalog service",
)

@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB and initialize Beanie
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product],
    )
    print("Connected to MongoDB and Beanie initialized.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}

# Include routers later
