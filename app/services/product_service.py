# app/services/product_service.py
from app.models.product import Product

async def get_product_by_id(product_id: str) -> Product | None:
    """Fetch a single product by its ObjectId (string)."""
    return await Product.get(product_id)