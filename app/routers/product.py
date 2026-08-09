from typing import List, Optional

from fastapi import APIRouter, Query
from beanie import PydanticObjectId

from app.models.product import Product
from app.services.product_service import get_products

router = APIRouter()

@router.get("/", response_model=List[Product])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    brand: Optional[str] = None,
):
    """
    List products with pagination and optional filtering by category/brand.
    """
    # Build the filter query
    filters = {}
    if category:
        filters["category"] = category
    if brand:
        filters["brand"] = brand

    # Use Beanie's `find` with the filters, then skip and limit
    products = await Product.find(filters).skip(skip).limit(limit).to_list()
    return products