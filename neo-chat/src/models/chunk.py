"""Text chunk data models."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ChunkBase(BaseModel):
    """Base chunk model."""
    
    document_id: UUID = Field(..., description="Document this chunk belongs to")
    user_id: UUID = Field(..., description="User who owns this chunk")
    content: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Index of chunk within document")
    token_count: Optional[int] = Field(None, description="Number of tokens in chunk")


class ChunkCreate(ChunkBase):
    """Model for creating a new chunk."""
    pass


class Chunk(ChunkBase):
    """Complete chunk model with database fields."""
    
    id: UUID = Field(..., description="Chunk's unique identifier")
    created_at: datetime = Field(..., description="Chunk creation timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "document_id": "123e4567-e89b-12d3-a456-426614174003",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "This is a chunk of text from a document.",
                "chunk_index": 0,
                "token_count": 10,
                "created_at": "2025-01-16T12:00:00Z"
            }
        }


class ChunkWithEmbedding(Chunk):
    """Chunk model with embedding vector."""
    
    embedding: list[float] = Field(..., description="768-dimensional embedding vector")
    similarity_score: Optional[float] = Field(
        None,
        description="Similarity score from vector search"
    )


class ChunkSearchResult(BaseModel):
    """Model for chunk search results."""
    
    chunks: list[ChunkWithEmbedding] = Field(..., description="Retrieved chunks")
    total_count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
