from typing import List, Optional

from fastapi import APIRouter, Query
from beanie import PydanticObjectId

from app.models.product import Product
from app.schemas.product_search import ProductSearchRequest

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
    Uses the 'active_created_desc' and 'category_brand' indexes.
    """
    filters = {"is_active": True}
    if category:
        filters["category"] = category
    if brand:
        filters["brand"] = brand

    products = await Product.find(filters).skip(skip).limit(limit).to_list()
    return products


@router.post("/search", response_model=List[Product])
async def search_products(request: ProductSearchRequest):
    """
    Rich product search with full‑text, filters, price ranges, and attribute filtering.
    """
    # Start with active products only
    filters = {"is_active": True}
    
    # 1. Full‑text search (uses the 'text_search' index)
    if request.text:
        filters["$text"] = {"$search": request.text}
    
    # 2. Category / Brand (uses the 'category_brand' index)
    if request.category:
        filters["category"] = request.category
    if request.brand:
        filters["brand"] = request.brand
    
    # 3. Price range (uses the 'price_asc' index)
    if request.min_price is not None or request.max_price is not None:
        price_filter = {}
        if request.min_price is not None:
            price_filter["$gte"] = request.min_price
        if request.max_price is not None:
            price_filter["$lte"] = request.max_price
        filters["price"] = price_filter
    
    # 4. Dynamic attribute filtering (uses regular index on attributes if any,
    #    but more importantly, demonstrates flexible schema querying)
    if request.attributes:
        for key, value in request.attributes.items():
            # Use dotted notation to filter inside the embedded dictionary
            filters[f"attributes.{key}"] = value
    
    # Execute the query
    products = await Product.find(filters).skip(request.skip).limit(request.limit).to_list()
    return products