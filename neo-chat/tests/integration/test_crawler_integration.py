"""Integration tests for web crawler service (T073)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.crawler_service import CrawlerService, CrawlerServiceError
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        GOOGLE_API_KEY="test-api-key",
        SUPABASE_URL="postgresql://test:test@localhost:5432/test",
        MIN_CHUNK_TOKENS=100,
        MAX_CHUNK_TOKENS=500
    )


@pytest.fixture
def crawler_service(settings):
    """Create crawler service instance."""
    return CrawlerService(settings)


class TestURLValidation:
    """Test URL validation functionality."""
    
    def test_validate_valid_http_url(self, crawler_service):
        """Test validation of valid HTTP URL."""
        is_valid, error = crawler_service.validate_url("http://example.com")
        assert is_valid is True
        assert error is None
    
    def test_validate_valid_https_url(self, crawler_service):
        """Test validation of valid HTTPS URL."""
        is_valid, error = crawler_service.validate_url("https://example.com/path")
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_protocol(self, crawler_service):
        """Test validation rejects invalid protocols."""
        is_valid, error = crawler_service.validate_url("ftp://example.com")
        assert is_valid is False
        assert "http or https" in error.lower()
    
    def test_validate_missing_domain(self, crawler_service):
        """Test validation rejects URLs without domain."""
        is_valid, error = crawler_service.validate_url("http://")
        assert is_valid is False
        assert "invalid" in error.lower()
    
    def test_validate_malformed_url(self, crawler_service):
        """Test validation rejects malformed URLs."""
        is_valid, error = crawler_service.validate_url("not-a-url")
        assert is_valid is False
        assert error is not None


class TestDomainBoundary:
    """Test domain boundary detection."""
    
    def test_get_domain_boundary(self, crawler_service):
        """Test extracting domain from URL."""
        domain = crawler_service.get_domain_boundary("https://example.com/path")
        assert domain == "example.com"
    
    def test_get_domain_with_subdomain(self, crawler_service):
        """Test extracting domain with subdomain."""
        domain = crawler_service.get_domain_boundary("https://blog.example.com/post")
        assert domain == "blog.example.com"
    
    def test_is_same_domain_true(self, crawler_service):
        """Test same domain detection returns True."""
        assert crawler_service.is_same_domain(
            "https://example.com/page1",
            "example.com"
        ) is True
    
    def test_is_same_domain_false(self, crawler_service):
        """Test different domain detection returns False."""
        assert crawler_service.is_same_domain(
            "https://other.com/page",
            "example.com"
        ) is False
    
    def test_is_same_domain_subdomain_mismatch(self, crawler_service):
        """Test subdomain mismatch is detected."""
        assert crawler_service.is_same_domain(
            "https://blog.example.com/page",
            "example.com"
        ) is False


class TestCrawlURL:
    """Test single URL crawling."""
    
    @pytest.mark.asyncio
    async def test_crawl_url_success(self, crawler_service):
        """Test successful URL crawling."""
        # Mock Crawl4AI
        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = "# Test Page\n\nThis is test content."
        mock_result.html = "<html><body>Test</body></html>"
        mock_result.metadata = {
            "title": "Test Page",
            "description": "Test description"
        }
        mock_result.links = {"internal": ["/page1", "/page2"]}
        
        with patch.object(crawler_service, 'AsyncWebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.__aenter__.return_value = mock_crawler
            mock_crawler.arun.return_value = mock_result
            mock_crawler_class.return_value = mock_crawler
            
            result = await crawler_service.crawl_url("https://example.com")
            
            assert result["content"] == "# Test Page\n\nThis is test content."
            assert result["metadata"]["title"] == "Test Page"
            assert result["metadata"]["url"] == "https://example.com"
            assert len(result["links"]) == 2
    
    @pytest.mark.asyncio
    async def test_crawl_url_failure(self, crawler_service):
        """Test URL crawling failure."""
        # Mock failed crawl
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Connection timeout"
        
        with patch.object(crawler_service, 'AsyncWebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.__aenter__.return_value = mock_crawler
            mock_crawler.arun.return_value = mock_result
            mock_crawler_class.return_value = mock_crawler
            
            with pytest.raises(CrawlerServiceError) as exc_info:
                await crawler_service.crawl_url("https://example.com")
            
            assert "Failed to crawl" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_crawl_url_not_installed(self, settings):
        """Test crawling when Crawl4AI not installed."""
        service = CrawlerService(settings)
        service.AsyncWebCrawler = None
        
        with pytest.raises(CrawlerServiceError) as exc_info:
            await service.crawl_url("https://example.com")
        
        assert "not installed" in str(exc_info.value).lower()


class TestCrawlWebsite:
    """Test website crawling with depth control."""
    
    @pytest.mark.asyncio
    async def test_crawl_website_single_page(self, crawler_service):
        """Test crawling single page website."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_job = Mock()
        mock_job.id = "test-job-id"
        mock_job.started_at = None
        mock_repo.update = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_job)
        crawler_service.crawl_job_repo = mock_repo
        
        # Mock chunking service
        crawler_service.chunking_service = AsyncMock()
        crawler_service.chunking_service.chunk_text = AsyncMock(return_value=[
            {"text": "chunk1", "metadata": {}},
            {"text": "chunk2", "metadata": {}}
        ])
        
        # Mock crawl_url
        async def mock_crawl_url(url):
            return {
                "content": "Test content",
                "metadata": {"url": url, "title": "Test"},
                "links": []
            }
        
        crawler_service.crawl_url = mock_crawl_url
        
        result = await crawler_service.crawl_website(
            job_id="test-job-id",
            start_url="https://example.com",
            max_depth=1,
            max_pages=10
        )
        
        assert result["success"] is True
        assert result["pages_crawled"] == 1
        assert result["chunks_created"] == 2
    
    @pytest.mark.asyncio
    async def test_crawl_website_respects_max_pages(self, crawler_service):
        """Test that crawling respects max_pages limit."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_job = Mock()
        mock_job.id = "test-job-id"
        mock_job.started_at = None
        mock_repo.update = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_job)
        crawler_service.crawl_job_repo = mock_repo
        
        # Mock chunking service
        crawler_service.chunking_service = AsyncMock()
        crawler_service.chunking_service.chunk_text = AsyncMock(return_value=[])
        
        # Mock crawl_url to return many links
        async def mock_crawl_url(url):
            return {
                "content": "Test",
                "metadata": {"url": url},
                "links": [f"/page{i}" for i in range(20)]  # Many links
            }
        
        crawler_service.crawl_url = mock_crawl_url
        
        result = await crawler_service.crawl_website(
            job_id="test-job-id",
            start_url="https://example.com",
            max_depth=5,
            max_pages=3  # Limit to 3 pages
        )
        
        assert result["pages_crawled"] <= 3
    
    @pytest.mark.asyncio
    async def test_crawl_website_respects_domain_boundary(self, crawler_service):
        """Test that crawling stays within domain."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_job = Mock()
        mock_job.id = "test-job-id"
        mock_job.started_at = None
        mock_repo.update = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_job)
        crawler_service.crawl_job_repo = mock_repo
        
        # Mock chunking service
        crawler_service.chunking_service = AsyncMock()
        crawler_service.chunking_service.chunk_text = AsyncMock(return_value=[])
        
        crawled_urls = []
        
        # Mock crawl_url to track what gets crawled
        async def mock_crawl_url(url):
            crawled_urls.append(url)
            return {
                "content": "Test",
                "metadata": {"url": url},
                "links": ["https://example.com/page1", "https://other.com/page2"]
            }
        
        crawler_service.crawl_url = mock_crawl_url
        
        await crawler_service.crawl_website(
            job_id="test-job-id",
            start_url="https://example.com",
            max_depth=2,
            max_pages=10
        )
        
        # Should only crawl example.com URLs, not other.com
        for url in crawled_urls:
            assert "example.com" in url


class TestRobotsTxt:
    """Test robots.txt checking."""
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_allowed(self, crawler_service):
        """Test robots.txt allows crawling."""
        # This is a basic test - in real scenarios, mock the RobotFileParser
        result = await crawler_service.check_robots_txt("https://example.com")
        # Should default to True if can't check
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_error_defaults_allowed(self, crawler_service):
        """Test that errors in robots.txt checking default to allowed."""
        with patch('urllib.robotparser.RobotFileParser') as mock_parser:
            mock_parser.side_effect = Exception("Network error")
            
            result = await crawler_service.check_robots_txt("https://example.com")
            assert result is True  # Should default to allowed on error
