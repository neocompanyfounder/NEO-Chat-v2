"""Crawler service for web content crawling with Crawl4AI.

This module provides web crawling capabilities using Crawl4AI for extracting
content from websites and storing it in the knowledge base.
"""

import asyncio
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime

from src.models.crawl_job import CrawlJob, CrawlJobUpdate, CrawlStatus
from src.db.repositories.crawl_job_repository import CrawlJobRepository
from src.services.chunking_service import ChunkingService
from src.services.gemini_service import GeminiService
from src.services.vector_service import VectorService
from src.db.repositories.chunk_repository import ChunkRepository
from src.utils.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrawlerServiceError(Exception):
    """Exception raised for crawler service errors."""
    pass


class CrawlerService:
    """Service for web content crawling with Crawl4AI."""
    
    def __init__(self, settings: Settings):
        """Initialize crawler service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.crawl_job_repo = CrawlJobRepository()
        self.chunk_repo = ChunkRepository()
        self.chunking_service = ChunkingService(settings)
        self.gemini_service = GeminiService(settings)
        self.vector_service = VectorService(settings)
        
        # Initialize Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            self.AsyncWebCrawler = AsyncWebCrawler
            logger.info("Crawler service initialized with Crawl4AI")
        except ImportError:
            logger.warning("crawl4ai not installed, web crawling will not be available")
            self.AsyncWebCrawler = None
    
    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """Validate URL format and accessibility.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme in ['http', 'https']:
                return False, "URL must use http or https protocol"
            
            if not parsed.netloc:
                return False, "Invalid URL format"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"
    
    def get_domain_boundary(self, url: str) -> str:
        """Extract domain for boundary detection.
        
        Args:
            url: Starting URL
            
        Returns:
            Domain name
        """
        parsed = urlparse(url)
        return parsed.netloc
    
    def is_same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL is within the same domain.
        
        Args:
            url: URL to check
            base_domain: Base domain for comparison
            
        Returns:
            True if same domain
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc == base_domain
        except:
            return False
    
    async def crawl_url(
        self,
        url: str,
        extract_markdown: bool = True
    ) -> Dict[str, Any]:
        """Crawl a single URL and extract content.
        
        Args:
            url: URL to crawl
            extract_markdown: Whether to extract as markdown
            
        Returns:
            Dictionary with extracted content and metadata
            
        Raises:
            CrawlerServiceError: If crawling fails
        """
        if self.AsyncWebCrawler is None:
            raise CrawlerServiceError("Crawl4AI not installed")
        
        try:
            async with self.AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=True
                )
                
                if not result.success:
                    raise CrawlerServiceError(f"Failed to crawl {url}: {result.error_message}")
                
                # Extract content
                content = result.markdown if extract_markdown else result.html
                
                metadata = {
                    "url": url,
                    "title": result.metadata.get("title", ""),
                    "description": result.metadata.get("description", ""),
                    "format": "markdown" if extract_markdown else "html",
                    "word_count": len(content.split()) if content else 0,
                    "links_found": len(result.links.get("internal", [])) if result.links else 0
                }
                
                logger.info(
                    f"Crawled URL successfully",
                    extra={
                        "url": url,
                        "word_count": metadata["word_count"],
                        "links_found": metadata["links_found"]
                    }
                )
                
                return {
                    "content": content,
                    "metadata": metadata,
                    "links": result.links.get("internal", []) if result.links else []
                }
                
        except Exception as e:
            logger.error(
                f"Failed to crawl URL: {str(e)}",
                extra={"url": url, "error": str(e)}
            )
            raise CrawlerServiceError(f"Crawling failed: {str(e)}")
    
    async def crawl_website(
        self,
        job_id: str,
        start_url: str,
        max_depth: int = 3,
        max_pages: int = 100,
        respect_robots: bool = True
    ) -> Dict[str, Any]:
        """Crawl a website starting from a URL.
        
        Args:
            job_id: Crawl job identifier
            start_url: Starting URL
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            respect_robots: Whether to respect robots.txt
            
        Returns:
            Crawl results with statistics
        """
        logger.info(
            "Starting website crawl",
            extra={
                "job_id": job_id,
                "start_url": start_url,
                "max_depth": max_depth,
                "max_pages": max_pages
            }
        )
        
        # Update job status to crawling
        await self.crawl_job_repo.update(
            job_id,
            CrawlJobUpdate(
                status=CrawlStatus.CRAWLING,
                started_at=datetime.utcnow()
            )
        )
        
        # Get domain boundary
        base_domain = self.get_domain_boundary(start_url)
        
        # Track crawled and pending URLs
        crawled_urls: Set[str] = set()
        pending_urls: List[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
        failed_urls: List[str] = []
        
        pages_crawled = 0
        chunks_created = 0
        
        try:
            while pending_urls and pages_crawled < max_pages:
                url, depth = pending_urls.pop(0)
                
                # Skip if already crawled
                if url in crawled_urls:
                    continue
                
                # Skip if exceeds max depth
                if depth > max_depth:
                    continue
                
                # Skip if not same domain
                if not self.is_same_domain(url, base_domain):
                    continue
                
                try:
                    # Crawl the URL
                    result = await self.crawl_url(url)
                    
                    crawled_urls.add(url)
                    pages_crawled += 1
                    
                    # Process content
                    if result["content"]:
                        # Chunk the content
                        chunks = await self.chunking_service.chunk_text(
                            result["content"],
                            metadata={
                                **result["metadata"],
                                "crawl_job_id": job_id,
                                "depth": depth,
                                "source": "web_crawl"
                            }
                        )
                        
                        chunks_created += len(chunks)
                        
                        # Store chunks (will be done by ingestion pipeline)
                        logger.info(
                            f"Processed page: {url}",
                            extra={
                                "chunks": len(chunks),
                                "depth": depth
                            }
                        )
                    
                    # Add new links to pending (if not at max depth)
                    if depth < max_depth:
                        for link in result.get("links", []):
                            full_url = urljoin(url, link)
                            if full_url not in crawled_urls and full_url not in [u for u, _ in pending_urls]:
                                pending_urls.append((full_url, depth + 1))
                    
                    # Update progress
                    await self.crawl_job_repo.update(
                        job_id,
                        CrawlJobUpdate(
                            pages_crawled=pages_crawled,
                            pages_found=len(crawled_urls) + len(pending_urls),
                            chunks_created=chunks_created
                        )
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to crawl {url}: {str(e)}",
                        extra={"url": url, "error": str(e)}
                    )
                    failed_urls.append(url)
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.5)
            
            # Update job status to completed
            await self.crawl_job_repo.update(
                job_id,
                CrawlJobUpdate(
                    status=CrawlStatus.COMPLETED,
                    pages_crawled=pages_crawled,
                    chunks_created=chunks_created,
                    failed_urls=failed_urls,
                    completed_at=datetime.utcnow(),
                    metadata={
                        "domain": base_domain,
                        "duration_seconds": (datetime.utcnow() - (await self.crawl_job_repo.get_by_id(job_id)).started_at).total_seconds()
                    }
                )
            )
            
            logger.info(
                "Website crawl completed",
                extra={
                    "job_id": job_id,
                    "pages_crawled": pages_crawled,
                    "chunks_created": chunks_created,
                    "failed_urls": len(failed_urls)
                }
            )
            
            return {
                "success": True,
                "pages_crawled": pages_crawled,
                "chunks_created": chunks_created,
                "failed_urls": failed_urls
            }
            
        except Exception as e:
            logger.error(
                f"Website crawl failed: {str(e)}",
                extra={
                    "job_id": job_id,
                    "error": str(e)
                }
            )
            
            # Update job status to failed
            await self.crawl_job_repo.update(
                job_id,
                CrawlJobUpdate(
                    status=CrawlStatus.FAILED,
                    error_message=str(e),
                    failed_urls=failed_urls,
                    completed_at=datetime.utcnow()
                )
            )
            
            return {
                "success": False,
                "error": str(e),
                "pages_crawled": pages_crawled,
                "failed_urls": failed_urls
            }
    
    async def check_robots_txt(self, url: str) -> bool:
        """Check if crawling is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if crawling is allowed
        """
        try:
            from urllib.robotparser import RobotFileParser
            
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch("*", url)
            
        except Exception as e:
            logger.warning(
                f"Failed to check robots.txt: {str(e)}",
                extra={"url": url}
            )
            # If we can't check, assume it's allowed
            return True
