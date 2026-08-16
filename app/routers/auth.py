# app/routers/auth.py
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from slowapi import Limiter

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.core.dependencies import get_current_user  # we'll define this in Part E

router = APIRouter(prefix="/auth", tags=["authentication"])

# ---------- Request/Response Schemas ----------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    email: EmailStr
    role: str

# ---------- Endpoints ----------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_user(user_data: UserRegister):
    """Register a new user. The first user ever registered becomes an admin."""
    
    # 1. Check if the email already exists
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 2. Determine role: First user is admin, everyone else is readonly
    # This is a handy pattern for demos; you can change it later.
    total_users = await User.count()
    role = "admin" if total_users == 0 else "readonly"
    
    # 3. Hash the password and create the user
    hashed = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        role=role,
        is_active=True,
    )
    await user.insert()
    
    # 4. Generate a JWT for immediate login
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(access_token=access_token)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login_user(creds: UserLogin):
    """Authenticate and receive a JWT access token."""
    # 1. Find user by email
    user = await User.find_one(User.email == creds.email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Verify password
    if not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generate token
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_my_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Return the currently authenticated user's info."""
    return UserResponse(email=current_user.email, role=current_user.role)