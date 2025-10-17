"""End-to-end tests for web crawling journey (T074, T075)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.crew_manager import CrewManager
from src.agents.tool_agent import ToolAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.response_agent import ResponseAgent
from src.services.crawler_service import CrawlerService
from src.services.whatsapp_service import WhatsAppService
from src.services.knowledge_base import KnowledgeBaseService
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        GOOGLE_API_KEY="test-api-key",
        SUPABASE_URL="postgresql://test:test@localhost:5432/test",
        EVOLUTION_API_URL="http://localhost:8080",
        EVOLUTION_API_KEY="test-key",
        EVOLUTION_INSTANCE_NAME="test-instance",
        MIN_CHUNK_TOKENS=100,
        MAX_CHUNK_TOKENS=500
    )


@pytest.fixture
def mock_whatsapp_service():
    """Create mock WhatsApp service."""
    service = AsyncMock(spec=WhatsAppService)
    service.send_text_message = AsyncMock()
    return service


@pytest.fixture
def mock_knowledge_base_service():
    """Create mock knowledge base service."""
    service = AsyncMock(spec=KnowledgeBaseService)
    service.search = AsyncMock(return_value=[
        {
            "text": "Information from crawled website",
            "metadata": {"url": "https://example.com/page1"}
        }
    ])
    service.store_conversation = AsyncMock()
    return service


@pytest.fixture
def mock_crawler_service(settings):
    """Create mock crawler service."""
    service = AsyncMock(spec=CrawlerService)
    
    # Mock validate_url
    service.validate_url = Mock(return_value=(True, None))
    
    # Mock crawl_job_repo
    mock_repo = AsyncMock()
    mock_job = Mock()
    mock_job.id = "test-crawl-job-123"
    mock_repo.create = AsyncMock(return_value=mock_job)
    service.crawl_job_repo = mock_repo
    
    # Mock crawl_website
    service.crawl_website = AsyncMock(return_value={
        "success": True,
        "pages_crawled": 5,
        "chunks_created": 15,
        "failed_urls": []
    })
    
    return service


@pytest.fixture
def mock_retrieval_agent(mock_knowledge_base_service):
    """Create mock retrieval agent."""
    agent = AsyncMock(spec=RetrievalAgent)
    agent.search_knowledge_base = AsyncMock(return_value=[
        {
            "text": "Information from crawled website",
            "metadata": {"url": "https://example.com/page1"}
        }
    ])
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def mock_response_agent():
    """Create mock response agent."""
    agent = AsyncMock(spec=ResponseAgent)
    agent.generate_response = AsyncMock(
        return_value="Based on the crawled website, here's the answer..."
    )
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def tool_agent(
    mock_knowledge_base_service,
    mock_whatsapp_service,
    mock_crawler_service
):
    """Create tool agent with mocked services."""
    agent = ToolAgent(
        knowledge_base_service=mock_knowledge_base_service,
        whatsapp_service=mock_whatsapp_service,
        rag_ingestion_service=None,
        crawler_service=mock_crawler_service
    )
    return agent


@pytest.fixture
def crew_manager(
    mock_retrieval_agent,
    mock_response_agent,
    tool_agent
):
    """Create crew manager with mocked agents."""
    return CrewManager(
        retrieval_agent=mock_retrieval_agent,
        response_agent=mock_response_agent,
        tool_agent=tool_agent
    )


class TestWebCrawlE2E:
    """End-to-end tests for web crawling user journey."""
    
    @pytest.mark.asyncio
    async def test_complete_web_crawl_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test complete journey: Send URL → Crawl → Notification → Query → Response.
        
        This is the main E2E test for User Story 3 (T075).
        """
        user_id = "test-user-123"
        phone_number = "+1234567890"
        url = "https://example.com"
        
        # Step 1: User sends URL via WhatsApp
        result = await crew_manager.process_web_crawl(
            user_id=user_id,
            phone_number=phone_number,
            url=url
        )
        
        # Verify crawl was initiated
        assert result["success"] is True
        assert result["url"] == url
        assert result["pages_crawled"] == 5
        assert result["chunks_created"] == 15
        
        # Verify initial notification was sent
        assert mock_whatsapp_service.send_text_message.call_count >= 1
        first_call = mock_whatsapp_service.send_text_message.call_args_list[0]
        assert "Starting to crawl" in first_call[1]["message"]
        
        # Verify completion notification was sent
        last_call = mock_whatsapp_service.send_text_message.call_args_list[-1]
        assert "completed" in last_call[1]["message"].lower()
        assert "5" in last_call[1]["message"]  # pages crawled
        assert "15" in last_call[1]["message"]  # chunks created
        
        # Step 2: User asks question about crawled content
        query_result = await crew_manager.process_simple_message(
            user_id=user_id,
            phone_number=phone_number,
            message="What did you learn from that website?"
        )
        
        # Verify response includes crawled content
        assert query_result["success"] is True
        assert "crawled website" in query_result["response"].lower()
    
    @pytest.mark.asyncio
    async def test_web_crawl_with_invalid_url(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test web crawl with invalid URL."""
        # Mock invalid URL
        mock_crawler_service.validate_url = Mock(
            return_value=(False, "Invalid URL format")
        )
        
        result = await crew_manager.process_web_crawl(
            user_id="test-user",
            phone_number="+1234567890",
            url="not-a-valid-url"
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Invalid URL" in result["error"]
        
        # Verify error notification was sent
        assert mock_whatsapp_service.send_text_message.called
        error_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "failed" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_web_crawl_with_crawl_failure(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test web crawl when crawling fails."""
        # Mock crawl failure
        mock_crawler_service.crawl_website = AsyncMock(return_value={
            "success": False,
            "error": "Connection timeout",
            "pages_crawled": 0,
            "failed_urls": ["https://example.com"]
        })
        
        result = await crew_manager.process_web_crawl(
            user_id="test-user",
            phone_number="+1234567890",
            url="https://example.com"
        )
        
        # Verify failure handling
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
        
        # Verify error notification
        assert mock_whatsapp_service.send_text_message.call_count >= 2
        error_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "failed" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_web_crawl_with_partial_success(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test web crawl with partial success (some pages fail)."""
        # Mock partial success
        mock_crawler_service.crawl_website = AsyncMock(return_value={
            "success": True,
            "pages_crawled": 3,
            "chunks_created": 8,
            "failed_urls": ["https://example.com/broken1", "https://example.com/broken2"]
        })
        
        result = await crew_manager.process_web_crawl(
            user_id="test-user",
            phone_number="+1234567890",
            url="https://example.com"
        )
        
        # Verify partial success is treated as success
        assert result["success"] is True
        assert result["pages_crawled"] == 3
        assert result["chunks_created"] == 8
        
        # Verify success notification
        success_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "completed" in success_msg.lower()
    
    @pytest.mark.asyncio
    async def test_web_crawl_depth_and_page_limits(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test web crawl with custom depth and page limits."""
        result = await crew_manager.process_web_crawl(
            user_id="test-user",
            phone_number="+1234567890",
            url="https://example.com",
            max_depth=5,
            max_pages=200
        )
        
        # Verify custom parameters were passed
        mock_crawler_service.crawl_website.assert_called_once()
        call_kwargs = mock_crawler_service.crawl_website.call_args[1]
        assert call_kwargs["max_depth"] == 5
        assert call_kwargs["max_pages"] == 200
    
    @pytest.mark.asyncio
    async def test_multiple_urls_in_sequence(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_crawler_service
    ):
        """Test crawling multiple URLs in sequence."""
        urls = [
            "https://example.com",
            "https://another-site.com",
            "https://third-site.com"
        ]
        
        results = []
        for url in urls:
            result = await crew_manager.process_web_crawl(
                user_id="test-user",
                phone_number="+1234567890",
                url=url
            )
            results.append(result)
        
        # Verify all crawls succeeded
        assert all(r["success"] for r in results)
        assert len(results) == 3
        
        # Verify notifications for each crawl
        assert mock_whatsapp_service.send_text_message.call_count >= 6  # 2 per crawl


class TestURLDetection:
    """Test URL detection in webhook messages."""
    
    def test_extract_single_url(self):
        """Test extracting single URL from message."""
        from src.api.routes.webhook import extract_urls
        
        text = "Check out this website: https://example.com"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com"
    
    def test_extract_multiple_urls(self):
        """Test extracting multiple URLs from message."""
        from src.api.routes.webhook import extract_urls
        
        text = "Visit https://example.com and http://another.com for info"
        urls = extract_urls(text)
        
        assert len(urls) == 2
        assert "example.com" in urls[0]
        assert "another.com" in urls[1]
    
    def test_extract_url_with_path(self):
        """Test extracting URL with path and query."""
        from src.api.routes.webhook import extract_urls
        
        text = "See https://example.com/path/to/page?param=value"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert "path/to/page" in urls[0]
        assert "param=value" in urls[0]
    
    def test_extract_no_urls(self):
        """Test message with no URLs."""
        from src.api.routes.webhook import extract_urls
        
        text = "This is just a regular message with no links"
        urls = extract_urls(text)
        
        assert len(urls) == 0
    
    def test_extract_urls_ignores_invalid(self):
        """Test that invalid URL-like text is ignored."""
        from src.api.routes.webhook import extract_urls
        
        text = "Contact us at email@example.com or visit www.example.com"
        urls = extract_urls(text)
        
        # Should not extract email or www without protocol
        assert len(urls) == 0


class TestWebCrawlIntegration:
    """Integration tests for web crawl components."""
    
    @pytest.mark.asyncio
    async def test_tool_agent_web_crawl(
        self,
        tool_agent,
        mock_crawler_service
    ):
        """Test tool agent web crawl processing."""
        result = await tool_agent.process_web_crawl(
            user_id="test-user",
            url="https://example.com",
            max_depth=3,
            max_pages=50
        )
        
        assert result["success"] is True
        assert "job_id" in result
        assert result["pages_crawled"] == 5
        assert result["chunks_created"] == 15
    
    @pytest.mark.asyncio
    async def test_tool_agent_web_crawl_without_service(
        self,
        mock_knowledge_base_service,
        mock_whatsapp_service
    ):
        """Test tool agent when crawler service not available."""
        agent = ToolAgent(
            knowledge_base_service=mock_knowledge_base_service,
            whatsapp_service=mock_whatsapp_service,
            crawler_service=None  # No crawler service
        )
        
        result = await agent.process_web_crawl(
            user_id="test-user",
            url="https://example.com"
        )
        
        assert result["success"] is False
        assert "not available" in result["error"].lower()
