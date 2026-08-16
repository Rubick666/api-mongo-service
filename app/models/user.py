from typing import Optional

from beanie import Document, IndexModel
from pydantic import EmailStr, Field
from pymongo import ASCENDING

class User(Document):
    """User model for authentication and role-based access."""
    email: EmailStr = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Bcrypt-hashed password")
    
    # Role-based access control
    # 'admin' can do everything; 'readonly' can only LIST and SEARCH.
    role: str = Field("readonly", pattern="^(admin|readonly)$")
    
    is_active: bool = Field(default=True)
    
    class Settings:
        name = "users"
        
        # Ensure email uniqueness at the database level
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True, name="email_unique")
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
            }
        }