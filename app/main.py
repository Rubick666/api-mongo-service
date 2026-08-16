from fastapi import FastAPI
from fastapi.responses import JSONResponse
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.models.product import Product
from app.models.user import User          # add User model
from app.routers import products, auth
from pymongo import AsyncMongoClient


app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB-backed product catalog service",
)


@app.on_event("startup")
async def startup_event():
    client = AsyncMongoClient(settings.mongo_uri)

    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product],
    )

    print("Connected to MongoDB and Beanie initialized.")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}


# Include the products router
app.include_router(
    product.router,
    prefix="/products",
    tags=["products"],
)

# 1. Setup rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB-backed product catalog service",
)

# 2. Register the rate limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product, User],   # add User
    )
    await Product.create_indexes()
    await User.create_indexes()            # ensures unique email index is created
    print("Connected to MongoDB and Beanie initialized.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}

# 3. Include routers
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(auth.router)            # no prefix needed; router has /auth internally