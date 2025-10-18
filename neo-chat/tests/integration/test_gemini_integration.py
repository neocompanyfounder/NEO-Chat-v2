"""Integration tests for Gemini API integration.

Tests the Gemini service integration for LLM inference and embeddings.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.gemini_service import GeminiService
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        EVOLUTION_API_URL="http://test-evolution-api:8080",
        EVOLUTION_API_KEY="test-api-key",
        EVOLUTION_INSTANCE_NAME="test-instance",
        EVOLUTION_TIMEOUT=10,
        GOOGLE_API_KEY="test-google-key",
        GEMINI_MODEL="gemini-2.0-flash-exp",
        GEMINI_EMBEDDING_MODEL="text-embedding-004",
        GEMINI_TIMEOUT=30,
        SUPABASE_URL="postgresql://test:test@localhost:5432/test",
        SUPABASE_SERVICE_ROLE_KEY="test-service-key",
        SUPABASE_ANON_KEY="test-anon-key",
        SUPABASE_TIMEOUT=5,
        APP_ENV="test",
        LOG_LEVEL="DEBUG",
        MAX_FILE_SIZE_MB=16,
        MAX_CONCURRENT_USERS=100,
        GEMINI_RATE_LIMIT_PER_MIN=60,
        WHATSAPP_RATE_LIMIT_PER_MIN=60,
        MAX_RETRIES=5,
        RETRY_BACKOFF_BASE=1,
        VECTOR_SIMILARITY_THRESHOLD=0.7,
        VECTOR_TOP_K=5,
        MAX_CONTEXT_TOKENS=8000,
        MIN_CHUNK_TOKENS=100,
        MAX_CHUNK_TOKENS=2000,
        MAX_CRAWL_PAGES=100,
        CRAWL_TIMEOUT_MINUTES=5,
        CRAWL_RATE_LIMIT_SECONDS=1
    )


@pytest.fixture
def gemini_service(settings):
    """Create Gemini service instance."""
    return GeminiService(settings)


@pytest.mark.asyncio
class TestGeminiIntegration:
    """Integration tests for Gemini service."""
    
    async def test_generate_response_success(self, gemini_service):
        """Test generating a response successfully."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.text = "This is a test response from Gemini."
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 10
            mock_response.usage_metadata.candidates_token_count = 8
            mock_generate.return_value = mock_response
            
            # Generate response
            result = await gemini_service.generate_response(
                prompt="Hello, how are you?",
                context=None
            )
            
            # Verify
            assert result is not None
            assert "response" in result
            assert result["response"] == "This is a test response from Gemini."
            assert "metadata" in result
            mock_generate.assert_called_once()
    
    async def test_generate_response_with_context(self, gemini_service):
        """Test generating response with context."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = MagicMock()
            mock_response.text = "Based on the context, here's my answer."
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 50
            mock_response.usage_metadata.candidates_token_count = 20
            mock_generate.return_value = mock_response
            
            # Generate response with context
            context = [
                {"content": "Previous conversation context"},
                {"content": "User uploaded document about Python"}
            ]
            
            result = await gemini_service.generate_response(
                prompt="What did I upload?",
                context=context
            )
            
            # Verify
            assert result is not None
            assert "response" in result
            assert "metadata" in result
            assert result["metadata"]["has_context"] is True
    
    async def test_generate_response_with_retry(self, gemini_service):
        """Test response generation with retry on failure."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            # Mock failure then success
            mock_generate.side_effect = [
                Exception("API rate limit exceeded"),
                MagicMock(
                    text="Success after retry",
                    usage_metadata=MagicMock(
                        prompt_token_count=10,
                        candidates_token_count=5
                    )
                )
            ]
            
            # Generate response (should retry)
            result = await gemini_service.generate_response(
                prompt="Test retry",
                context=None
            )
            
            # Verify retry worked
            assert result is not None
            assert result["response"] == "Success after retry"
            assert mock_generate.call_count == 2
    
    async def test_generate_response_empty_prompt(self, gemini_service):
        """Test generating response with empty prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await gemini_service.generate_response(
                prompt="",
                context=None
            )
    
    async def test_generate_response_timeout(self, gemini_service):
        """Test response generation with timeout."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            import asyncio
            mock_generate.side_effect = asyncio.TimeoutError("Request timeout")
            
            # Should raise after retries
            with pytest.raises(Exception, match="timeout|failed"):
                await gemini_service.generate_response(
                    prompt="Test timeout",
                    context=None
                )
    
    async def test_generate_embedding_success(self, gemini_service):
        """Test generating embeddings successfully."""
        with patch('google.generativeai.embed_content') as mock_embed:
            # Mock successful embedding
            mock_embed.return_value = {
                "embedding": [0.1, 0.2, 0.3] * 256  # 768 dimensions
            }
            
            # Generate embedding
            result = await gemini_service.generate_embedding(
                text="This is a test text for embedding"
            )
            
            # Verify
            assert result is not None
            assert len(result) == 768
            assert all(isinstance(x, float) for x in result)
            mock_embed.assert_called_once()
    
    async def test_generate_embedding_batch(self, gemini_service):
        """Test generating embeddings in batch."""
        with patch('google.generativeai.embed_content') as mock_embed:
            # Mock batch embedding
            mock_embed.return_value = {
                "embedding": [0.1, 0.2, 0.3] * 256
            }
            
            # Generate embeddings for multiple texts
            texts = [
                "First text chunk",
                "Second text chunk",
                "Third text chunk"
            ]
            
            results = []
            for text in texts:
                embedding = await gemini_service.generate_embedding(text)
                results.append(embedding)
            
            # Verify
            assert len(results) == 3
            assert all(len(emb) == 768 for emb in results)
            assert mock_embed.call_count == 3
    
    async def test_generate_embedding_empty_text(self, gemini_service):
        """Test generating embedding with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await gemini_service.generate_embedding(text="")
    
    async def test_rate_limiting(self, gemini_service):
        """Test rate limiting for Gemini API."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = MagicMock()
            mock_response.text = "Response"
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 5
            mock_response.usage_metadata.candidates_token_count = 5
            mock_generate.return_value = mock_response
            
            # Send multiple requests quickly
            for i in range(5):
                result = await gemini_service.generate_response(
                    prompt=f"Test message {i}",
                    context=None
                )
                assert result is not None
            
            # Verify all requests were made
            assert mock_generate.call_count == 5
    
    async def test_context_window_limit(self, gemini_service):
        """Test handling of context window limits."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = MagicMock()
            mock_response.text = "Response with truncated context"
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 8000
            mock_response.usage_metadata.candidates_token_count = 100
            mock_generate.return_value = mock_response
            
            # Create large context
            large_context = [
                {"content": "A" * 1000} for _ in range(100)
            ]
            
            # Generate response (should handle context truncation)
            result = await gemini_service.generate_response(
                prompt="Summarize the context",
                context=large_context
            )
            
            # Verify
            assert result is not None
            assert "response" in result
    
    async def test_structured_output(self, gemini_service):
        """Test generating structured output."""
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            # Mock structured response
            mock_response = MagicMock()
            mock_response.text = '{"action": "search", "query": "test"}'
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 15
            mock_response.usage_metadata.candidates_token_count = 10
            mock_generate.return_value = mock_response
            
            # Generate structured response
            result = await gemini_service.generate_response(
                prompt="Extract action and query from: 'search for test'",
                context=None
            )
            
            # Verify
            assert result is not None
            assert "response" in result
            
            # Parse JSON response
            import json
            parsed = json.loads(result["response"])
            assert "action" in parsed
            assert "query" in parsed
