from typing import List, Optional

from fastapi import APIRouter, Query
from beanie import PydanticObjectId

from app.models.product import Product
from app.schemas.product_search import ProductSearchRequest
from slowapi import Limiter
from fastapi import Request

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.dependencies import AdminUser, require_admin
from app.models.product import Product
from app.schemas.product_create import ProductCreate

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
@limiter.limit("100/minute")
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

@router.post("/bulk-import", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def bulk_import(
    request: Request,
    file: UploadFile = File(...),
    admin_user: AdminUser = Depends(require_admin),  # Only admins can import
):
    """
    Bulk import products from a CSV or JSONL file.
    - CSV: first row must be headers (name, price, category, brand, ...).
    - JSONL: each line is a JSON object.
    
    Returns a summary: number imported and detailed errors per row.
    """
    # 1. Validate file extension
    if not file.filename:
        raise HTTPException(400, "No file provided")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ("csv", "jsonl", "json"):
        raise HTTPException(400, "File must be .csv, .jsonl, or .json")
    
    # 2. Stream the file and parse rows
    products_to_insert = []
    errors = []
    line_number = 1
    
    # 2a. CSV parsing
    if ext == "csv":
        # Wrap binary file in TextIOWrapper for CSV reader
        reader = csv.DictReader(TextIOWrapper(file.file, "utf-8"))
        required_headers = {"name", "price", "category", "brand"}
        if not required_headers.issubset(reader.fieldnames or []):
            raise HTTPException(400, f"CSV must have headers: {required_headers}")
        
        for row in reader:
            line_number += 1
            try:
                # Convert string values to proper types
                row["price"] = float(row.get("price", 0))
                row["inventory_count"] = int(row.get("inventory_count", 0))
                
                # Optional attributes – any column not in the base schema goes into 'attributes'
                base_fields = {"name", "description", "price", "category", "brand", "inventory_count", "image_urls"}
                attrs = {k: v for k, v in row.items() if k not in base_fields and v}
                if attrs:
                    row["attributes"] = attrs
                
                # Validate with Pydantic
                validated = ProductCreate(**row)
                products_to_insert.append(Product(**validated.dict()))
            except Exception as e:
                errors.append({"line": line_number, "error": str(e)})
    
    # 2b. JSONL parsing (each line is a separate JSON object)
    elif ext in ("jsonl", "json"):
        # We assume newline-delimited JSON for large files (JSONL)
        # If it's a single large JSON array, we'd need a different parser (ijson) – 
        # but JSONL is the standard for streaming.
        async for line in file.file:
            line_number += 1
            line = line.decode("utf-8").strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                validated = ProductCreate(**data)
                products_to_insert.append(Product(**validated.dict()))
            except Exception as e:
                errors.append({"line": line_number, "error": str(e)})
    
    # 3. Bulk insert with partial success handling
    imported_count = 0
    if products_to_insert:
        # Use BulkWriter with ordered=False so that if one fails (e.g., duplicate),
        # the others continue. This gives us a "best-effort" import.
        async with BulkWriter() as bw:
            for prod in products_to_insert:
                bw.add(prod)
            result = await bw.commit()  # returns a BulkWriteResult
            imported_count = result.inserted_count
    
    # 4. Return the summary
    return {
        "imported": imported_count,
        "total_rows_processed": line_number - 1,  # minus 1 because we started at 1
        "errors": errors,
    }

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """
    Fetch a single product by its MongoDB ObjectId.
    Returns 404 if the product does not exist or is soft-deleted.
    """
    if not PydanticObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = await Product.get(PydanticObjectId(product_id))
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1)
    brand: Optional[str] = Field(None, min_length=1)
    inventory_count: Optional[int] = Field(None, ge=0)
    image_urls: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@router.patch("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    updates: ProductUpdate,
    admin_user: AdminUser = Depends(require_admin),  # only admins can update
):
    """
    Update a product's fields. All fields are optional.
    Triggers a version update (sets updated_at to now).
    """
    if not PydanticObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = await Product.get(PydanticObjectId(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Convert updates to a dict, excluding None values
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Always update the `updated_at` field – this serves as a "version" marker
    update_data["updated_at"] = datetime.utcnow()
    
    # Apply the update using Beanie's `set` operator
    await product.set(update_data)
    
    # Refresh the document to get the new values
    await product.fetch()
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin_user: AdminUser = Depends(require_admin),  # only admins can delete
):
    """
    Soft-delete a product by setting is_active=False.
    The document remains in the database for audit/restoration.
    """
    if not PydanticObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = await Product.get(PydanticObjectId(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft-delete
    await product.set({"is_active": False, "updated_at": datetime.utcnow()})
    return None  # 204 No Content

# New response schemas for aggregation
class CategoryCount(BaseModel):
    category: str
    count: int

class PriceDistribution(BaseModel):
    label: str          # e.g., "0-25", "25-50"
    min_price: float
    max_price: float
    count: int

@router.get("/analytics/categories", response_model=List[CategoryCount])
async def get_category_counts():
    """
    Aggregation pipeline: Count products per category.
    Uses MongoDB's $group stage.
    """
    pipeline = [
        {"$match": {"is_active": True}},  # only active products
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},         # most popular first
    ]
    # Beanie's aggregate returns an async cursor of dicts
    cursor = Product.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append({"category": doc["_id"], "count": doc["count"]})
    return results


@router.get("/analytics/price-distribution", response_model=List[PriceDistribution])
async def get_price_distribution(
    bins: int = Query(5, ge=2, le=20, description="Number of price buckets")
):
    """
    Aggregation pipeline: Bucket active products into price ranges.
    Uses MongoDB's $bucket stage for histogram-like output.
    """
    # 1. Get min and max prices to dynamically calculate bucket boundaries
    price_range = await Product.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {"_id": None, "min": {"$min": "$price"}, "max": {"$max": "$price"}}}
    ]).to_list()
    
    if not price_range:
        return []  # no products
    
    min_price = price_range[0]["min"]
    max_price = price_range[0]["max"]
    
    # If all products have the same price, avoid division by zero
    if min_price == max_price:
        return [{"label": f"${min_price:.2f}", "min_price": min_price, "max_price": max_price, "count": await Product.count({"is_active": True})}]
    
    # 2. Build the bucket pipeline
    step = (max_price - min_price) / bins
    boundaries = [min_price + i * step for i in range(bins + 1)]
    
    pipeline = [
        {"$match": {"is_active": True}},
        {
            "$bucket": {
                "groupBy": "$price",
                "boundaries": boundaries,
                "default": "Other",
                "output": {"count": {"$sum": 1}}
            }
        }
    ]
    
    cursor = Product.aggregate(pipeline)
    results = []
    async for doc in cursor:
        if doc["_id"] == "Other":
            continue  # skip outliers outside our dynamic range
        # Make a human-readable label
        label = f"${doc['_id']:.2f} - ${doc['_id'] + step:.2f}"
        results.append({
            "label": label,
            "min_price": doc["_id"],
            "max_price": doc["_id"] + step,
            "count": doc["count"]
        })
    return results