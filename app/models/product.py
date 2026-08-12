from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document, PydanticObjectId
from pydantic import Field

class Product(Document):
    # Core fields
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    inventory_count: int = Field(0, ge=0)
    
    # Image URLs (e.g. product photos)
    image_urls: List[str] = Field(default_factory=list)
    
    # Flexible attributes – this is where MongoDB shines
    # e.g. {"brake_pad_material": "ceramic", "fits_vehicles": ["Honda Civic"]}
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document, IndexModel
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, TEXT

class Product(Document):
    # Core fields
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    inventory_count: int = Field(0, ge=0)
    
    # Image URLs
    image_urls: List[str] = Field(default_factory=list)
    
    # Flexible attributes
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    class Settings:
        name = "products"
        
        # 1. Validation schema (unchanged)
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
        
        # 2. Indexes – this is where the performance story lives
        indexes = [
            # Text index for full‑text search on name and description
            IndexModel(
                [("name", TEXT), ("description", TEXT)],
                name="text_search"
            ),
            
            # Compound index for the most common filtered listing pattern
            IndexModel(
                [("category", ASCENDING), ("brand", ASCENDING)],
                name="category_brand"
            ),
            
            # Single‑field index for price range queries
            IndexModel(
                [("price", ASCENDING)],
                name="price_asc"
            ),
            
            # Compound index for active products sorted by creation date
            # Used for default listing (GET /products) when no filters are applied
            IndexModel(
                [("is_active", ASCENDING), ("created_at", DESCENDING)],
                name="active_created_desc"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.brand})"

    class Config:
        json_schema_extra = {
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

    def __str__(self) -> str:
        return f"{self.name} ({self.brand})"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ceramic Brake Pads",
                "description": "High-performance ceramic brake pads for all-season driving",
                "price": 49.99,
                "category": "Brakes",
                "brand": "AutoStop",
                "inventory_count": 120,
                "image_urls": ["https://example.com/pad1.jpg"],
                "attributes": {
                    "material": "ceramic",
                    "fits_vehicles": ["Honda Civic 2020", "Toyota Camry 2021"],
                    "warranty_years": 2,
                },
                "is_active": True,
            }
        }