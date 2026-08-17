from fastapi import FastAPI
from fastapi.responses import JSONResponse
from beanie import init_beanie
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.models.product import Product
from app.models.user import User          # add User model
from app.routers import product, auth
from pymongo import AsyncMongoClient
from app.core.limiter import limiter

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
    client = AsyncMongoClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product, User],   # add User
    )
    print("Connected to MongoDB and Beanie initialized.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}

# 3. Include routers
app.include_router(product.router, prefix="/products", tags=["products"])
app.include_router(auth.router)            # no prefix needed; router has /auth internally