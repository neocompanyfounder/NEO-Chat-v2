"""User data models."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user model."""
    
    phone_number: str = Field(
        ...,
        description="User's phone number in E.164 format",
        example="+1234567890"
    )


class UserCreate(UserBase):
    """Model for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Model for updating a user."""
    
    phone_number: Optional[str] = Field(
        None,
        description="Updated phone number in E.164 format"
    )


class User(UserBase):
    """Complete user model with database fields."""
    
    id: UUID = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "phone_number": "+1234567890",
                "created_at": "2025-01-16T12:00:00Z",
                "updated_at": "2025-01-16T12:00:00Z"
            }
        }
