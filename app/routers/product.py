import csv
import json
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional

from beanie import BulkWriter, PydanticObjectId
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from app.core.dependencies import AdminUser
from app.core.limiter import limiter
from app.models.product import Product
from app.schemas.product_create import ProductCreate
from app.schemas.product_search import ProductSearchRequest


router = APIRouter()


# ============================================================
# LIST PRODUCTS
# ============================================================

@router.get("/", response_model=List[Product])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    brand: Optional[str] = None,
):
    """
    List products with pagination and optional filtering
    by category and/or brand.
    """
    filters = {"is_active": True}

    if category:
        filters["category"] = category

    if brand:
        filters["brand"] = brand

    products = (
        await Product.find(filters)
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    return products


# ============================================================
# SEARCH PRODUCTS
# ============================================================

@router.post("/search", response_model=List[Product])
@limiter.limit("100/minute")
async def search_products(
    request: Request,
    search_request: ProductSearchRequest,
):
    """
    Rich product search with:

    - Full-text search
    - Category filtering
    - Brand filtering
    - Price ranges
    - Dynamic attribute filtering
    """
    filters = {
        "is_active": True
    }

    # --------------------------------------------------------
    # 1. Full-text search
    # --------------------------------------------------------

    if search_request.text:
        filters["$text"] = {
            "$search": search_request.text
        }

    # --------------------------------------------------------
    # 2. Category / Brand
    # --------------------------------------------------------

    if search_request.category:
        filters["category"] = search_request.category

    if search_request.brand:
        filters["brand"] = search_request.brand

    # --------------------------------------------------------
    # 3. Price range
    # --------------------------------------------------------

    if (
        search_request.min_price is not None
        or search_request.max_price is not None
    ):
        price_filter = {}

        if search_request.min_price is not None:
            price_filter["$gte"] = search_request.min_price

        if search_request.max_price is not None:
            price_filter["$lte"] = search_request.max_price

        filters["price"] = price_filter

    # --------------------------------------------------------
    # 4. Dynamic attributes
    # --------------------------------------------------------

    if search_request.attributes:
        for key, value in search_request.attributes.items():
            filters[f"attributes.{key}"] = value

    # --------------------------------------------------------
    # Execute query
    # --------------------------------------------------------

    products = (
        await Product.find(filters)
        .skip(search_request.skip)
        .limit(search_request.limit)
        .to_list()
    )

    return products


# ============================================================
# BULK IMPORT
# ============================================================

@router.post("/bulk-import", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def bulk_import(
    request: Request,
    admin_user: AdminUser,
    file: UploadFile = File(...),
):
    """
    Bulk import products from CSV, JSONL, or JSON.

    CSV:
        First row must contain:
        name, price, category, brand

    JSONL:
        One JSON object per line.

    JSON:
        Either a single JSON object or a JSON array.
    """

    # --------------------------------------------------------
    # 1. Validate filename
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext not in {"csv", "jsonl", "json"}:
        raise HTTPException(
            status_code=400,
            detail="File must be .csv, .jsonl, or .json",
        )

    # --------------------------------------------------------
    # 2. Read uploaded file
    # --------------------------------------------------------

    content = await file.read()

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded",
        )

    products_to_insert: List[Product] = []
    errors: List[Dict[str, Any]] = []

    total_rows_processed = 0

    # ========================================================
    # CSV
    # ========================================================

    if ext == "csv":

        reader = csv.DictReader(
            StringIO(text_content)
        )

        required_headers = {
            "name",
            "price",
            "category",
            "brand",
        }

        actual_headers = set(
            reader.fieldnames or []
        )

        if not required_headers.issubset(actual_headers):
            missing = required_headers - actual_headers

            raise HTTPException(
                status_code=400,
                detail=(
                    "CSV is missing required headers: "
                    f"{sorted(missing)}"
                ),
            )

        for line_number, row in enumerate(
            reader,
            start=2,
        ):
            total_rows_processed += 1

            try:
                # ------------------------------------------------
                # Convert price
                # ------------------------------------------------

                row["price"] = float(
                    row.get("price") or 0
                )

                # ------------------------------------------------
                # Convert inventory
                # ------------------------------------------------

                row["inventory_count"] = int(
                    row.get("inventory_count") or 0
                )

                # ------------------------------------------------
                # Convert image_urls
                #
                # Example CSV:
                #
                # image_urls =
                # https://a.com/1.jpg,https://a.com/2.jpg
                # ------------------------------------------------

                if row.get("image_urls"):
                    row["image_urls"] = [
                        url.strip()
                        for url in row["image_urls"].split(",")
                        if url.strip()
                    ]
                else:
                    row.pop("image_urls", None)

                # ------------------------------------------------
                # Dynamic attributes
                # ------------------------------------------------

                base_fields = {
                    "name",
                    "description",
                    "price",
                    "category",
                    "brand",
                    "inventory_count",
                    "image_urls",
                    "attributes",
                    "is_active",
                }

                attrs = {
                    key: value
                    for key, value in row.items()
                    if key not in base_fields
                    and value not in (None, "")
                }

                if attrs:
                    row["attributes"] = attrs

                # ------------------------------------------------
                # Validate using ProductCreate
                # ------------------------------------------------

                validated = ProductCreate(**row)

                product = Product(
                    **validated.model_dump()
                )

                products_to_insert.append(product)

            except Exception as exc:
                errors.append(
                    {
                        "line": line_number,
                        "error": str(exc),
                    }
                )

    # ========================================================
    # JSON / JSONL
    # ========================================================

    else:

        # --------------------------------------------------------
        # JSONL
        # --------------------------------------------------------

        if ext == "jsonl":

            for line_number, raw_line in enumerate(
                text_content.splitlines(),
                start=1,
            ):
                if not raw_line.strip():
                    continue

                total_rows_processed += 1

                try:
                    data = json.loads(
                        raw_line
                    )

                    if not isinstance(data, dict):
                        raise ValueError(
                            "Each JSONL line must contain "
                            "a JSON object"
                        )

                    validated = ProductCreate(
                        **data
                    )

                    product = Product(
                        **validated.model_dump()
                    )

                    products_to_insert.append(product)

                except Exception as exc:
                    errors.append(
                        {
                            "line": line_number,
                            "error": str(exc),
                        }
                    )

        # --------------------------------------------------------
        # Regular JSON
        # --------------------------------------------------------

        else:

            try:
                data = json.loads(
                    text_content
                )

                # A JSON file may contain:
                #
                # [
                #   {...},
                #   {...}
                # ]
                #
                # or:
                #
                # {...}

                if isinstance(data, dict):
                    data = [data]

                if not isinstance(data, list):
                    raise ValueError(
                        "JSON file must contain "
                        "an object or an array of objects"
                    )

                for index, item in enumerate(
                    data,
                    start=1,
                ):
                    total_rows_processed += 1

                    try:
                        if not isinstance(item, dict):
                            raise ValueError(
                                "Each JSON item must "
                                "be an object"
                            )

                        validated = ProductCreate(
                            **item
                        )

                        product = Product(
                            **validated.model_dump()
                        )

                        products_to_insert.append(
                            product
                        )

                    except Exception as exc:
                        errors.append(
                            {
                                "line": index,
                                "error": str(exc),
                            }
                        )

            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid JSON file: "
                        f"{str(exc)}"
                    ),
                )

    # ========================================================
    # 3. Bulk insert
    # ========================================================

    imported_count = 0

    if products_to_insert:

        try:
            async with BulkWriter(
                ordered=False
            ) as bulk_writer:

                for product in products_to_insert:
                    bulk_writer.add(
                        product
                    )

                result = await bulk_writer.commit()

                imported_count = (
                    result.inserted_count
                )

        except Exception as exc:

            # If MongoDB-level bulk insertion fails,
            # preserve the already collected validation errors.
            errors.append(
                {
                    "line": None,
                    "error": (
                        "Bulk database insertion failed: "
                        f"{str(exc)}"
                    ),
                }
            )

    # ========================================================
    # 4. Return summary
    # ========================================================

    return {
        "imported": imported_count,
        "total_rows_processed": total_rows_processed,
        "errors": errors,
    }


# ============================================================
# ANALYTICS - CATEGORY COUNTS
#
# IMPORTANT:
# These routes must appear BEFORE /{product_id}
# ============================================================

class CategoryCount(BaseModel):
    category: str
    count: int


@router.get(
    "/analytics/categories",
    response_model=List[CategoryCount],
)
async def get_category_counts():
    """
    Count active products per category.
    """

    pipeline = [
        {
            "$match": {
                "is_active": True
            }
        },
        {
            "$group": {
                "_id": "$category",
                "count": {
                    "$sum": 1
                },
            }
        },
        {
            "$sort": {
                "count": -1
            }
        },
    ]

    cursor = Product.aggregate(
        pipeline
    )

    results = []

    async for document in cursor:
        results.append(
            {
                "category": document["_id"],
                "count": document["count"],
            }
        )

    return results


# ============================================================
# ANALYTICS - PRICE DISTRIBUTION
# ============================================================

class PriceDistribution(BaseModel):
    label: str
    min_price: float
    max_price: float
    count: int


@router.get(
    "/analytics/price-distribution",
    response_model=List[PriceDistribution],
)
async def get_price_distribution(
    bins: int = Query(
        5,
        ge=2,
        le=20,
        description="Number of price buckets",
    ),
):
    """
    Bucket active products into dynamic price ranges.
    """

    # --------------------------------------------------------
    # 1. Find min/max prices
    # --------------------------------------------------------

    price_range = (
        await Product.aggregate(
            [
                {
                    "$match": {
                        "is_active": True
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "min": {
                            "$min": "$price"
                        },
                        "max": {
                            "$max": "$price"
                        },
                    }
                },
            ]
        ).to_list()
    )

    if not price_range:
        return []

    min_price = price_range[0]["min"]
    max_price = price_range[0]["max"]

    # --------------------------------------------------------
    # 2. All products have the same price
    # --------------------------------------------------------

    if min_price == max_price:

        count = await Product.find(
            {
                "is_active": True
            }
        ).count()

        return [
            {
                "label": f"${min_price:.2f}",
                "min_price": min_price,
                "max_price": max_price,
                "count": count,
            }
        ]

    # --------------------------------------------------------
    # 3. Calculate bucket boundaries
    # --------------------------------------------------------

    step = (max_price - min_price) / bins

    boundaries = [
        min_price + i * step
        for i in range(bins)
    ]

    boundaries.append(max_price + 1e-12)

    # --------------------------------------------------------
    # 4. MongoDB $bucket aggregation
    # --------------------------------------------------------

    pipeline = [
        {
            "$match": {
                "is_active": True
            }
        },
        {
            "$bucket": {
                "groupBy": "$price",
                "boundaries": boundaries,
                "default": "Other",
                "output": {
                    "count": {
                        "$sum": 1
                    }
                },
            }
        },
    ]

    cursor = Product.aggregate(
        pipeline
    )

    results = []

    async for document in cursor:

        if document["_id"] == "Other":
            continue

        bucket_min = float(
            document["_id"]
        )

        bucket_max = bucket_min + step

        results.append(
            {
                "label": (
                    f"${bucket_min:.2f} - "
                    f"${bucket_max:.2f}"
                ),
                "min_price": bucket_min,
                "max_price": bucket_max,
                "count": document["count"],
            }
        )

    return results


# ============================================================
# GET SINGLE PRODUCT
# ============================================================

@router.get(
    "/{product_id}",
    response_model=Product,
)
async def get_product(
    product_id: str,
):
    """
    Fetch a single active product by MongoDB ObjectId.
    """

    if not PydanticObjectId.is_valid(
        product_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID format",
        )

    product = await Product.get(
        PydanticObjectId(product_id)
    )

    if not product or not product.is_active:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# ============================================================
# UPDATE PRODUCT SCHEMA
# ============================================================

class ProductUpdate(BaseModel):
    """
    Schema for updating a product.
    All fields are optional.
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
    )

    description: Optional[str] = None

    price: Optional[float] = Field(
        None,
        gt=0,
    )

    category: Optional[str] = Field(
        None,
        min_length=1,
    )

    brand: Optional[str] = Field(
        None,
        min_length=1,
    )

    inventory_count: Optional[int] = Field(
        None,
        ge=0,
    )

    image_urls: Optional[List[str]] = None

    attributes: Optional[
        Dict[str, Any]
    ] = None

    is_active: Optional[bool] = None


# ============================================================
# UPDATE PRODUCT
# ============================================================

@router.patch(
    "/{product_id}",
    response_model=Product,
)
async def update_product(
    product_id: str,
    updates: ProductUpdate,
    admin_user: AdminUser,
):
    """
    Update product fields.
    Only administrators can perform this operation.
    """

    if not PydanticObjectId.is_valid(
        product_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID format",
        )

    product = await Product.get(
        PydanticObjectId(product_id)
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Pydantic v2
    update_data = {
        key: value
        for key, value in updates.model_dump(
            exclude_unset=True
        ).items()
        if value is not None
    }

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No valid fields to update",
        )

    # Update timestamp
    update_data[
        "updated_at"
    ] = datetime.now(timezone.utc)

    await product.set(
        update_data
    )

    await product.fetch()

    return product


# ============================================================
# DELETE PRODUCT
# ============================================================

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: str,
    admin_user: AdminUser,
):
    """
    Soft-delete a product.

    The document remains in MongoDB but is marked
    as inactive.
    """

    if not PydanticObjectId.is_valid(
        product_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID format",
        )

    product = await Product.get(
        PydanticObjectId(product_id)
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    await product.set(
        {
            "is_active": False,
            "updated_at": datetime.now(
                timezone.utc
            ),
        }
    )

    return None