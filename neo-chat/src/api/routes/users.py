"""User management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from src.db.repositories.user_repository import UserRepository
from src.db import get_db_client
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.utils.phone_utils import normalize_phone_number

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    """User creation request."""
    phone_number: str = Field(..., description="Phone number in E.164 format (e.g., +966556265604)")
    name: Optional[str] = Field(None, description="User's name (optional)")


class UserResponse(BaseModel):
    """User response."""
    id: str
    phone_number: str
    name: Optional[str]
    created_at: str
    updated_at: str


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user or get existing user.
    
    This endpoint will:
    - Create a new user if the phone number doesn't exist
    - Return the existing user if the phone number is already registered
    
    Args:
        user_data: User creation data with phone number and optional name
        
    Returns:
        User information including ID
    """
    try:
        # Normalize phone number to E.164 format
        normalized_phone = normalize_phone_number(user_data.phone_number)
        
        logger.info(
            "User registration request",
            extra={
                "phone_number": normalized_phone,
                "user_name": user_data.name
            }
        )
        
        # Get or create user
        db_client = get_db_client()
        user_repo = UserRepository(db_client)
        
        # Check if user exists
        existing_user = await user_repo.get_by_phone(normalized_phone)
        
        if existing_user:
            logger.info(
                "User already exists",
                extra={
                    "user_id": existing_user["id"],
                    "phone_number": normalized_phone
                }
            )
            return UserResponse(**existing_user)
        
        # Create new user
        user = await user_repo.get_or_create(
            phone_number=normalized_phone,
            name=user_data.name
        )
        
        logger.info(
            "User registered successfully",
            extra={
                "user_id": user["id"],
                "phone_number": normalized_phone
            }
        )
        
        return UserResponse(**user)
        
    except Exception as e:
        logger.error(
            "User registration failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "phone_number": user_data.phone_number
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"User registration failed: {str(e)}"
        )


@router.get("/{phone_number}", response_model=UserResponse)
async def get_user(phone_number: str):
    """Get user by phone number.
    
    Args:
        phone_number: Phone number in E.164 format (e.g., +966556265604)
        
    Returns:
        User information
    """
    try:
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        logger.info(
            "User lookup request",
            extra={"phone_number": normalized_phone}
        )
        
        # Get user
        db_client = get_db_client()
        user_repo = UserRepository(db_client)
        user = await user_repo.get_by_phone(normalized_phone)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {normalized_phone}"
            )
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "User lookup failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "phone_number": phone_number
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"User lookup failed: {str(e)}"
        )


@router.get("/")
async def list_users(limit: int = 10, offset: int = 0):
    """List all users.
    
    Args:
        limit: Maximum number of users to return (default: 10)
        offset: Number of users to skip (default: 0)
        
    Returns:
        List of users
    """
    try:
        db_client = get_db_client()
        user_repo = UserRepository(db_client)
        
        # Get users from database
        users = await user_repo.list_users(limit=limit, offset=offset)
        
        logger.info(
            "Users listed",
            extra={
                "count": len(users),
                "limit": limit,
                "offset": offset
            }
        )
        
        return {
            "users": users,
            "count": len(users),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(
            "User list failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"User list failed: {str(e)}"
        )
