"""Document model for file uploads and knowledge base content.

This module defines the Document Pydantic model for tracking uploaded files
and their processing status in the knowledge base.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Document model for uploaded files."""
    
    id: Optional[str] = Field(None, description="Unique document identifier")
    user_id: str = Field(..., description="User who uploaded the document")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentType = Field(..., description="Type of document")
    file_size: int = Field(..., description="File size in bytes", gt=0)
    mime_type: str = Field(..., description="MIME type of the file")
    storage_path: Optional[str] = Field(None, description="Path where file is stored")
    
    # Processing metadata
    status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current processing status"
    )
    chunks_count: int = Field(default=0, description="Number of chunks extracted", ge=0)
    processing_error: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is within limits (16MB)."""
        max_size = 16 * 1024 * 1024  # 16MB in bytes
        if v > max_size:
            raise ValueError(f"File size {v} bytes exceeds maximum allowed size of {max_size} bytes (16MB)")
        return v
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename is not empty."""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()
    
    @field_validator('mime_type')
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Validate MIME type format."""
        if not v or '/' not in v:
            raise ValueError("Invalid MIME type format")
        return v.lower()
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "doc-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123",
                "filename": "presentation.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "storage_path": "/uploads/user-123/presentation.pdf",
                "status": "completed",
                "chunks_count": 42,
                "uploaded_at": "2025-01-17T10:00:00Z",
                "processed_at": "2025-01-17T10:00:15Z",
                "metadata": {
                    "pages": 10,
                    "language": "en"
                }
            }
        }


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    
    user_id: str = Field(..., description="User who uploaded the document")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentType = Field(..., description="Type of document")
    file_size: int = Field(..., description="File size in bytes", gt=0)
    mime_type: str = Field(..., description="MIME type of the file")
    storage_path: Optional[str] = Field(None, description="Path where file is stored")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class DocumentUpdate(BaseModel):
    """Model for updating document status."""
    
    status: Optional[ProcessingStatus] = None
    chunks_count: Optional[int] = Field(None, ge=0)
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    metadata: Optional[dict] = None
