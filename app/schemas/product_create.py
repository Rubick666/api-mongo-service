from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    inventory_count: int = Field(0, ge=0)
    image_urls: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)