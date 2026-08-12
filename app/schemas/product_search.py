from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

class ProductSearchRequest(BaseModel):
    """Rich search request for product catalog."""
    
    text: Optional[str] = Field(
        None,
        description="Full‑text search over product name and description"
    )
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    
    min_price: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum price (inclusive)"
    )
    max_price: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum price (inclusive)"
    )
    
    attributes: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter by flexible attributes (e.g. {'material': 'ceramic'})"
    )
    
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Records per page")