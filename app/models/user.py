from typing import Optional

from beanie import Document
from pydantic import ConfigDict, EmailStr, Field
from pymongo import ASCENDING, IndexModel


class User(Document):
    email: EmailStr = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Bcrypt-hashed password")
    role: str = Field("readonly", pattern="^(admin|readonly)$")
    is_active: bool = Field(default=True)

    class Settings:
        name = "users"
        indexes = [IndexModel([("email", ASCENDING)], unique=True, name="email_unique")]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
            }
        }
    )