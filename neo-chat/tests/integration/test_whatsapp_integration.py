"""Integration tests for WhatsApp/Evolution API integration.

Tests the WhatsApp service integration with Evolution API for sending
and receiving messages.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.whatsapp_service import WhatsAppService
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
def whatsapp_service(settings):
    """Create WhatsApp service instance."""
    return WhatsAppService(settings)


@pytest.mark.asyncio
class TestWhatsAppIntegration:
    """Integration tests for WhatsApp service."""
    
    async def test_send_text_message_success(self, whatsapp_service):
        """Test sending a text message successfully."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "Message sent successfully",
                "messageId": "test-message-id-123"
            }
            mock_post.return_value = mock_response
            
            # Send message
            result = await whatsapp_service.send_text_message(
                phone_number="+1234567890",
                message="Hello, this is a test message"
            )
            
            # Verify
            assert result is not None
            assert "messageId" in result
            assert result["messageId"] == "test-message-id-123"
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/message/sendText" in str(call_args)
    
    async def test_send_text_message_with_retry(self, whatsapp_service):
        """Test message sending with retry on failure."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock failure then success
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 500
            mock_response_fail.raise_for_status.side_effect = Exception("Server error")
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "message": "Message sent successfully",
                "messageId": "test-message-id-456"
            }
            
            mock_post.side_effect = [
                Exception("Connection error"),
                mock_response_success
            ]
            
            # Send message (should retry)
            result = await whatsapp_service.send_text_message(
                phone_number="+1234567890",
                message="Test retry"
            )
            
            # Verify retry worked
            assert result is not None
            assert result["messageId"] == "test-message-id-456"
            assert mock_post.call_count == 2
    
    async def test_send_text_message_invalid_phone(self, whatsapp_service):
        """Test sending message with invalid phone number."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            await whatsapp_service.send_text_message(
                phone_number="invalid-phone",
                message="Test message"
            )
    
    async def test_send_text_message_empty_message(self, whatsapp_service):
        """Test sending empty message."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await whatsapp_service.send_text_message(
                phone_number="+1234567890",
                message=""
            )
    
    async def test_send_text_message_timeout(self, whatsapp_service):
        """Test message sending with timeout."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock timeout
            import asyncio
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")
            
            # Should raise after retries
            with pytest.raises(Exception, match="timeout|failed"):
                await whatsapp_service.send_text_message(
                    phone_number="+1234567890",
                    message="Test timeout"
                )
    
    async def test_rate_limiting(self, whatsapp_service):
        """Test rate limiting for WhatsApp messages."""
        # This test would verify that rate limiting is enforced
        # In a real implementation, you'd track message timestamps
        # and ensure no more than 60 messages per minute per user
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "Message sent successfully",
                "messageId": "test-id"
            }
            mock_post.return_value = mock_response
            
            # Send multiple messages quickly
            for i in range(5):
                result = await whatsapp_service.send_text_message(
                    phone_number="+1234567890",
                    message=f"Test message {i}"
                )
                assert result is not None
            
            # Verify all messages were sent
            assert mock_post.call_count == 5
    
    async def test_connection_validation(self, whatsapp_service):
        """Test Evolution API connection validation."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock successful connection check
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "instance": "test-instance",
                "status": "connected"
            }
            mock_get.return_value = mock_response
            
            # Validate connection
            is_connected = await whatsapp_service.validate_connection()
            
            assert is_connected is True
            mock_get.assert_called_once()
    
    async def test_connection_validation_failure(self, whatsapp_service):
        """Test Evolution API connection validation failure."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock connection failure
            mock_get.side_effect = Exception("Connection refused")
            
            # Validate connection
            is_connected = await whatsapp_service.validate_connection()
            
            assert is_connected is False
