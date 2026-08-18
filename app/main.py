from fastapi import FastAPI
from beanie import init_beanie
from pymongo import AsyncMongoClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.models.product import Product
from app.models.user import User
from app.routers import product, auth


# ---------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description="MongoDB-backed product catalog service",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

mongo_client = None


async def init_db():
    """
    Initialize MongoDB and Beanie.

    The database name comes from settings, which allows tests
    to use a separate database.
    """
    global mongo_client

    mongo_client = AsyncMongoClient(settings.mongo_uri)

    await init_beanie(
        database=mongo_client[settings.mongo_db_name],
        document_models=[
            Product,
            User,
        ],
    )

    print(
        f"Connected to MongoDB database: "
        f"{settings.mongo_db_name}"
    )


@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Startup complete.")


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "api-mongo-service",
    }


app.include_router(
    product.router,
    prefix="/products",
    tags=["products"],
)

app.include_router(auth.router)