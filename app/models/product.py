from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel


class Product(Document):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    inventory_count: int = Field(0, ge=0)
    image_urls: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    class Settings:
        name = "products"
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["name", "price", "category", "brand", "is_active"],
                "properties": {
                    "name": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "price": {"bsonType": "number"},
                    "category": {"bsonType": "string"},
                    "brand": {"bsonType": "string"},
                    "inventory_count": {"bsonType": "int"},
                    "image_urls": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "attributes": {"bsonType": "object"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "is_active": {"bsonType": "bool"},
                },
                "additionalProperties": False,
            }
        }
        indexes = [
            IndexModel([("name", TEXT), ("description", TEXT)], name="text_search"),
            IndexModel([("category", ASCENDING), ("brand", ASCENDING)], name="category_brand"),
            IndexModel([("price", ASCENDING)], name="price_asc"),
            IndexModel([("is_active", ASCENDING), ("created_at", DESCENDING)], name="active_created_desc"),
        ]

    # Pydantic v2 configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ceramic Brake Pads",
                "description": "High-performance ceramic brake pads...",
                "price": 49.99,
                "category": "Brakes",
                "brand": "AutoStop",
                "inventory_count": 120,
                "image_urls": ["https://example.com/pad1.jpg"],
                "attributes": {"material": "ceramic", "warranty_years": 2},
                "is_active": True,
            }
        }
    )