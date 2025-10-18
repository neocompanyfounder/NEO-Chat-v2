"""Message data models."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base message model."""
    
    user_id: UUID = Field(..., description="User who sent/received the message")
    message_id: str = Field(..., description="WhatsApp message ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional message metadata"
    )


class MessageCreate(MessageBase):
    """Model for creating a new message."""
    pass


class Message(MessageBase):
    """Complete message model with database fields."""
    
    id: UUID = Field(..., description="Message's unique identifier")
    created_at: datetime = Field(..., description="Message timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_id": "3EB0123456789ABCDEF",
                "role": "user",
                "content": "Hello, what can you help me with?",
                "metadata": {
                    "source": "whatsapp",
                    "timestamp": "1705420800"
                },
                "created_at": "2025-01-16T12:00:00Z"
            }
        }


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    
    messages: list[Message] = Field(..., description="List of messages in conversation")
    total_count: int = Field(..., description="Total number of messages")
    user_id: UUID = Field(..., description="User ID for the conversation")
