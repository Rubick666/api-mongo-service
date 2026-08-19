from fastapi import FastAPI
from beanie import init_beanie
from pymongo import AsyncMongoClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.models.product import Product
from app.models.user import User
from app.routers import product, auth


app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB‑backed product catalog service",
)

# Only attach limiter and handler when not testing
if not settings.testing:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


async def init_db():
    client = AsyncMongoClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product, User],
    )
    print(f"Connected to MongoDB database: {settings.mongo_db_name}")


@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Startup complete.")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-mongo-service"}


app.include_router(product.router, prefix="/products", tags=["products"])
app.include_router(auth.router)