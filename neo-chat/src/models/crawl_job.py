"""Crawl job model for web content crawling.

This module defines the CrawlJob Pydantic model for tracking web crawling
operations and their status.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, HttpUrl


class CrawlStatus(str, Enum):
    """Crawl job status."""
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlJob(BaseModel):
    """Crawl job model for web content crawling."""
    
    id: Optional[str] = Field(None, description="Unique crawl job identifier")
    user_id: str = Field(..., description="User who initiated the crawl")
    url: str = Field(..., description="Starting URL to crawl")
    
    # Crawl configuration
    max_depth: int = Field(default=3, description="Maximum crawl depth", ge=0, le=10)
    max_pages: int = Field(default=100, description="Maximum pages to crawl", ge=1, le=1000)
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    
    # Status and progress
    status: CrawlStatus = Field(
        default=CrawlStatus.PENDING,
        description="Current crawl status"
    )
    pages_crawled: int = Field(default=0, description="Number of pages crawled", ge=0)
    pages_found: int = Field(default=0, description="Number of pages found", ge=0)
    chunks_created: int = Field(default=0, description="Number of chunks created", ge=0)
    
    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if crawl failed")
    failed_urls: List[str] = Field(default_factory=list, description="URLs that failed to crawl")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Crawl start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Crawl completion timestamp")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        
        # Basic URL validation
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        return v
    
    @field_validator('max_depth')
    @classmethod
    def validate_max_depth(cls, v: int) -> int:
        """Validate max depth is reasonable."""
        if v < 0:
            raise ValueError("Max depth cannot be negative")
        if v > 10:
            raise ValueError("Max depth cannot exceed 10 (performance limit)")
        return v
    
    @field_validator('max_pages')
    @classmethod
    def validate_max_pages(cls, v: int) -> int:
        """Validate max pages is reasonable."""
        if v < 1:
            raise ValueError("Max pages must be at least 1")
        if v > 1000:
            raise ValueError("Max pages cannot exceed 1000 (performance limit)")
        return v
    
    def get_domain(self) -> str:
        """Extract domain from URL.
        
        Returns:
            Domain name
        """
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        return parsed.netloc
    
    def get_progress_percentage(self) -> float:
        """Calculate crawl progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.max_pages == 0:
            return 0.0
        return min(100.0, (self.pages_crawled / self.max_pages) * 100)
    
    def is_complete(self) -> bool:
        """Check if crawl is complete.
        
        Returns:
            True if crawl is completed or failed
        """
        return self.status in [CrawlStatus.COMPLETED, CrawlStatus.FAILED, CrawlStatus.CANCELLED]
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "crawl-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123",
                "url": "https://example.com",
                "max_depth": 3,
                "max_pages": 100,
                "respect_robots": True,
                "status": "completed",
                "pages_crawled": 42,
                "pages_found": 50,
                "chunks_created": 156,
                "created_at": "2025-01-17T10:00:00Z",
                "started_at": "2025-01-17T10:00:05Z",
                "completed_at": "2025-01-17T10:02:30Z",
                "metadata": {
                    "domain": "example.com",
                    "duration_seconds": 145
                }
            }
        }


class CrawlJobCreate(BaseModel):
    """Model for creating a new crawl job."""
    
    user_id: str = Field(..., description="User who initiated the crawl")
    url: str = Field(..., description="Starting URL to crawl")
    max_depth: int = Field(default=3, description="Maximum crawl depth", ge=0, le=10)
    max_pages: int = Field(default=100, description="Maximum pages to crawl", ge=1, le=1000)
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class CrawlJobUpdate(BaseModel):
    """Model for updating crawl job status."""
    
    status: Optional[CrawlStatus] = None
    pages_crawled: Optional[int] = Field(None, ge=0)
    pages_found: Optional[int] = Field(None, ge=0)
    chunks_created: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    failed_urls: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[dict] = None
