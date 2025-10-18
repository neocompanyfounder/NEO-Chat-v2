"""Crawl job repository for database operations.

This module provides CRUD operations for crawl jobs in the database.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from src.models.crawl_job import CrawlJob, CrawlJobCreate, CrawlJobUpdate, CrawlStatus
from src.db.supabase_client import get_supabase_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrawlJobRepository:
    """Repository for crawl job database operations."""
    
    def __init__(self):
        """Initialize crawl job repository."""
        self.client = get_supabase_client()
    
    async def create(self, crawl_job: CrawlJobCreate) -> CrawlJob:
        """Create a new crawl job record.
        
        Args:
            crawl_job: Crawl job creation data
            
        Returns:
            Created crawl job with ID
            
        Raises:
            Exception: If database operation fails
        """
        try:
            job_id = str(uuid.uuid4())
            
            async with self.client.acquire() as conn:
                query = """
                    INSERT INTO crawl_jobs (
                        id, user_id, url, max_depth, max_pages, respect_robots,
                        status, pages_crawled, pages_found, chunks_created,
                        created_at, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    job_id,
                    crawl_job.user_id,
                    crawl_job.url,
                    crawl_job.max_depth,
                    crawl_job.max_pages,
                    crawl_job.respect_robots,
                    CrawlStatus.PENDING.value,
                    0,
                    0,
                    0,
                    datetime.utcnow(),
                    crawl_job.metadata
                )
                
                logger.info(
                    "Crawl job created",
                    extra={
                        "job_id": job_id,
                        "user_id": crawl_job.user_id,
                        "url": crawl_job.url
                    }
                )
                
                return CrawlJob(**dict(row))
                
        except Exception as e:
            logger.error(
                f"Failed to create crawl job: {str(e)}",
                extra={
                    "user_id": crawl_job.user_id,
                    "url": crawl_job.url,
                    "error": str(e)
                }
            )
            raise
    
    async def get_by_id(self, job_id: str) -> Optional[CrawlJob]:
        """Get crawl job by ID.
        
        Args:
            job_id: Crawl job identifier
            
        Returns:
            Crawl job if found, None otherwise
        """
        try:
            async with self.client.acquire() as conn:
                query = "SELECT * FROM crawl_jobs WHERE id = $1"
                row = await conn.fetchrow(query, job_id)
                
                if row:
                    return CrawlJob(**dict(row))
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to get crawl job: {str(e)}",
                extra={"job_id": job_id, "error": str(e)}
            )
            raise
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[CrawlJob]:
        """Get all crawl jobs for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of crawl jobs
        """
        try:
            async with self.client.acquire() as conn:
                query = """
                    SELECT * FROM crawl_jobs
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, user_id, limit, offset)
                
                return [CrawlJob(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(
                f"Failed to get user crawl jobs: {str(e)}",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
    
    async def update(self, job_id: str, update: CrawlJobUpdate) -> Optional[CrawlJob]:
        """Update crawl job status and progress.
        
        Args:
            job_id: Crawl job identifier
            update: Update data
            
        Returns:
            Updated crawl job if found, None otherwise
        """
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            param_count = 1
            
            if update.status is not None:
                update_fields.append(f"status = ${param_count}")
                values.append(update.status.value)
                param_count += 1
            
            if update.pages_crawled is not None:
                update_fields.append(f"pages_crawled = ${param_count}")
                values.append(update.pages_crawled)
                param_count += 1
            
            if update.pages_found is not None:
                update_fields.append(f"pages_found = ${param_count}")
                values.append(update.pages_found)
                param_count += 1
            
            if update.chunks_created is not None:
                update_fields.append(f"chunks_created = ${param_count}")
                values.append(update.chunks_created)
                param_count += 1
            
            if update.error_message is not None:
                update_fields.append(f"error_message = ${param_count}")
                values.append(update.error_message)
                param_count += 1
            
            if update.failed_urls is not None:
                update_fields.append(f"failed_urls = ${param_count}")
                values.append(update.failed_urls)
                param_count += 1
            
            if update.started_at is not None:
                update_fields.append(f"started_at = ${param_count}")
                values.append(update.started_at)
                param_count += 1
            
            if update.completed_at is not None:
                update_fields.append(f"completed_at = ${param_count}")
                values.append(update.completed_at)
                param_count += 1
            
            if update.metadata is not None:
                update_fields.append(f"metadata = ${param_count}")
                values.append(update.metadata)
                param_count += 1
            
            if not update_fields:
                # No updates to perform
                return await self.get_by_id(job_id)
            
            values.append(job_id)
            
            async with self.client.acquire() as conn:
                query = f"""
                    UPDATE crawl_jobs
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                    RETURNING *
                """
                
                row = await conn.fetchrow(query, *values)
                
                if row:
                    logger.info(
                        "Crawl job updated",
                        extra={
                            "job_id": job_id,
                            "updates": update_fields
                        }
                    )
                    return CrawlJob(**dict(row))
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to update crawl job: {str(e)}",
                extra={"job_id": job_id, "error": str(e)}
            )
            raise
    
    async def delete(self, job_id: str) -> bool:
        """Delete a crawl job.
        
        Args:
            job_id: Crawl job identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.client.acquire() as conn:
                query = "DELETE FROM crawl_jobs WHERE id = $1"
                result = await conn.execute(query, job_id)
                
                deleted = result.split()[-1] == "1"
                
                if deleted:
                    logger.info(
                        "Crawl job deleted",
                        extra={"job_id": job_id}
                    )
                
                return deleted
                
        except Exception as e:
            logger.error(
                f"Failed to delete crawl job: {str(e)}",
                extra={"job_id": job_id, "error": str(e)}
            )
            raise
    
    async def delete_by_user(self, user_id: str) -> int:
        """Delete all crawl jobs for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of jobs deleted
        """
        try:
            async with self.client.acquire() as conn:
                query = "DELETE FROM crawl_jobs WHERE user_id = $1"
                result = await conn.execute(query, user_id)
                
                count = int(result.split()[-1])
                
                logger.info(
                    "User crawl jobs deleted",
                    extra={"user_id": user_id, "count": count}
                )
                
                return count
                
        except Exception as e:
            logger.error(
                f"Failed to delete user crawl jobs: {str(e)}",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
    
    async def get_pending_jobs(self, limit: int = 10) -> List[CrawlJob]:
        """Get pending crawl jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of pending crawl jobs
        """
        try:
            async with self.client.acquire() as conn:
                query = """
                    SELECT * FROM crawl_jobs
                    WHERE status = $1
                    ORDER BY created_at ASC
                    LIMIT $2
                """
                rows = await conn.fetch(query, CrawlStatus.PENDING.value, limit)
                
                return [CrawlJob(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(
                f"Failed to get pending crawl jobs: {str(e)}",
                extra={"error": str(e)}
            )
            raise
    
    async def get_active_jobs(self, user_id: Optional[str] = None) -> List[CrawlJob]:
        """Get active (crawling) jobs.
        
        Args:
            user_id: Optional user identifier to filter by
            
        Returns:
            List of active crawl jobs
        """
        try:
            async with self.client.acquire() as conn:
                if user_id:
                    query = """
                        SELECT * FROM crawl_jobs
                        WHERE status = $1 AND user_id = $2
                        ORDER BY started_at DESC
                    """
                    rows = await conn.fetch(query, CrawlStatus.CRAWLING.value, user_id)
                else:
                    query = """
                        SELECT * FROM crawl_jobs
                        WHERE status = $1
                        ORDER BY started_at DESC
                    """
                    rows = await conn.fetch(query, CrawlStatus.CRAWLING.value)
                
                return [CrawlJob(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(
                f"Failed to get active crawl jobs: {str(e)}",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
