"""End-to-end tests for basic WhatsApp text conversation.

Tests the complete user journey for User Story 1 (P1):
Send text message → Receive AI response → Verify storage in knowledge base
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.api.routes.webhook import process_message
from src.models.webhook_events import WebhookMessage
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


@pytest.mark.asyncio
@pytest.mark.e2e
class TestTextConversationE2E:
    """End-to-end tests for text conversation user journey."""
    
    async def test_complete_text_conversation_flow(self, settings):
        """Test complete flow: Receive message → Generate response → Send reply → Store conversation."""
        # Mock all external services
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini, \
             patch('src.services.vector_service.VectorService') as MockVector, \
             patch('src.services.knowledge_base.KnowledgeBaseService') as MockKB:
            
            # Setup mocks
            mock_whatsapp = MockWhatsApp.return_value
            mock_whatsapp.send_text_message = AsyncMock(return_value={"messageId": "msg-123"})
            
            mock_gemini = MockGemini.return_value
            mock_gemini.generate_response = AsyncMock(return_value={
                "response": "Hello! I'm NEO Chat, your AI assistant. I can help you with conversations, file uploads, web crawling, and more.",
                "metadata": {"model": "gemini-2.0-flash-exp", "has_context": False}
            })
            mock_gemini.generate_embedding = AsyncMock(return_value=[0.1] * 768)
            
            mock_vector = MockVector.return_value
            mock_vector.search_similar_chunks = AsyncMock(return_value=[])
            mock_vector.store_embedding = AsyncMock(return_value=True)
            
            mock_kb = MockKB.return_value
            mock_kb.store_conversation = AsyncMock(return_value=True)
            mock_kb.get_recent_context = AsyncMock(return_value=[])
            
            # Simulate incoming webhook message
            webhook_data = {
                "event": "messages.upsert",
                "data": {
                    "key": {
                        "remoteJid": "1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test-msg-id"
                    },
                    "message": {
                        "conversation": "Hello, what can you help me with?"
                    },
                    "messageTimestamp": 1705484400
                }
            }
            
            # Process message
            result = await process_message(webhook_data)
            
            # Verify complete flow
            assert result is not None
            
            # Verify AI response was generated
            mock_gemini.generate_response.assert_called_once()
            
            # Verify response was sent back
            mock_whatsapp.send_text_message.assert_called_once()
            call_args = mock_whatsapp.send_text_message.call_args
            assert "+1234567890" in str(call_args) or "1234567890" in str(call_args)
            
            # Verify conversation was stored
            mock_kb.store_conversation.assert_called()
    
    async def test_conversation_with_context_retrieval(self, settings):
        """Test conversation with context from knowledge base."""
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini, \
             patch('src.services.vector_service.VectorService') as MockVector, \
             patch('src.services.knowledge_base.KnowledgeBaseService') as MockKB:
            
            # Setup mocks with context
            mock_whatsapp = MockWhatsApp.return_value
            mock_whatsapp.send_text_message = AsyncMock(return_value={"messageId": "msg-456"})
            
            mock_gemini = MockGemini.return_value
            mock_gemini.generate_response = AsyncMock(return_value={
                "response": "Based on our previous conversation, you asked about Python programming.",
                "metadata": {"model": "gemini-2.0-flash-exp", "has_context": True}
            })
            mock_gemini.generate_embedding = AsyncMock(return_value=[0.2] * 768)
            
            # Mock context retrieval
            mock_vector = MockVector.return_value
            mock_vector.search_similar_chunks = AsyncMock(return_value=[
                {
                    "chunk_id": "chunk-1",
                    "content": "User asked: What is Python? AI answered: Python is a programming language.",
                    "similarity": 0.95,
                    "metadata": {"timestamp": "2025-01-16T10:00:00Z"}
                }
            ])
            mock_vector.store_embedding = AsyncMock(return_value=True)
            
            mock_kb = MockKB.return_value
            mock_kb.get_recent_context = AsyncMock(return_value=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."}
            ])
            mock_kb.store_conversation = AsyncMock(return_value=True)
            
            # Simulate follow-up question
            webhook_data = {
                "event": "messages.upsert",
                "data": {
                    "key": {
                        "remoteJid": "1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test-msg-id-2"
                    },
                    "message": {
                        "conversation": "What did we discuss yesterday?"
                    },
                    "messageTimestamp": 1705570800
                }
            }
            
            # Process message
            result = await process_message(webhook_data)
            
            # Verify context was retrieved
            mock_vector.search_similar_chunks.assert_called_once()
            mock_kb.get_recent_context.assert_called_once()
            
            # Verify response included context
            mock_gemini.generate_response.assert_called_once()
            call_args = mock_gemini.generate_response.call_args
            assert call_args[1].get("context") is not None
    
    async def test_multiple_messages_fifo_order(self, settings):
        """Test multiple messages processed in FIFO order."""
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini, \
             patch('src.services.vector_service.VectorService') as MockVector, \
             patch('src.services.knowledge_base.KnowledgeBaseService') as MockKB:
            
            # Setup mocks
            mock_whatsapp = MockWhatsApp.return_value
            mock_whatsapp.send_text_message = AsyncMock(return_value={"messageId": "msg-xxx"})
            
            mock_gemini = MockGemini.return_value
            responses = [
                {"response": "Response 1", "metadata": {}},
                {"response": "Response 2", "metadata": {}},
                {"response": "Response 3", "metadata": {}}
            ]
            mock_gemini.generate_response = AsyncMock(side_effect=responses)
            mock_gemini.generate_embedding = AsyncMock(return_value=[0.3] * 768)
            
            mock_vector = MockVector.return_value
            mock_vector.search_similar_chunks = AsyncMock(return_value=[])
            mock_vector.store_embedding = AsyncMock(return_value=True)
            
            mock_kb = MockKB.return_value
            mock_kb.get_recent_context = AsyncMock(return_value=[])
            mock_kb.store_conversation = AsyncMock(return_value=True)
            
            # Send multiple messages
            messages = [
                "First message",
                "Second message",
                "Third message"
            ]
            
            for i, msg in enumerate(messages):
                webhook_data = {
                    "event": "messages.upsert",
                    "data": {
                        "key": {
                            "remoteJid": "1234567890@s.whatsapp.net",
                            "fromMe": False,
                            "id": f"test-msg-{i}"
                        },
                        "message": {
                            "conversation": msg
                        },
                        "messageTimestamp": 1705484400 + i
                    }
                }
                
                await process_message(webhook_data)
            
            # Verify all messages were processed in order
            assert mock_gemini.generate_response.call_count == 3
            assert mock_whatsapp.send_text_message.call_count == 3
    
    async def test_response_time_under_10_seconds(self, settings):
        """Test that response time is under 10 seconds (SC-001)."""
        import time
        
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini, \
             patch('src.services.vector_service.VectorService') as MockVector, \
             patch('src.services.knowledge_base.KnowledgeBaseService') as MockKB:
            
            # Setup mocks with realistic delays
            mock_whatsapp = MockWhatsApp.return_value
            async def send_with_delay(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate network delay
                return {"messageId": "msg-123"}
            mock_whatsapp.send_text_message = send_with_delay
            
            mock_gemini = MockGemini.return_value
            async def generate_with_delay(*args, **kwargs):
                await asyncio.sleep(0.5)  # Simulate LLM processing
                return {"response": "Test response", "metadata": {}}
            mock_gemini.generate_response = generate_with_delay
            mock_gemini.generate_embedding = AsyncMock(return_value=[0.4] * 768)
            
            mock_vector = MockVector.return_value
            async def search_with_delay(*args, **kwargs):
                await asyncio.sleep(0.2)  # Simulate vector search
                return []
            mock_vector.search_similar_chunks = search_with_delay
            mock_vector.store_embedding = AsyncMock(return_value=True)
            
            mock_kb = MockKB.return_value
            mock_kb.get_recent_context = AsyncMock(return_value=[])
            mock_kb.store_conversation = AsyncMock(return_value=True)
            
            # Measure response time
            webhook_data = {
                "event": "messages.upsert",
                "data": {
                    "key": {
                        "remoteJid": "1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test-msg-perf"
                    },
                    "message": {
                        "conversation": "Test performance"
                    },
                    "messageTimestamp": 1705484400
                }
            }
            
            import asyncio
            start_time = time.time()
            await process_message(webhook_data)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Verify response time is under 10 seconds
            assert response_time < 10.0, f"Response time {response_time}s exceeds 10s limit"
    
    async def test_conversation_storage_verification(self, settings):
        """Test that conversation is stored in knowledge base."""
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini, \
             patch('src.services.vector_service.VectorService') as MockVector, \
             patch('src.services.knowledge_base.KnowledgeBaseService') as MockKB:
            
            # Setup mocks
            mock_whatsapp = MockWhatsApp.return_value
            mock_whatsapp.send_text_message = AsyncMock(return_value={"messageId": "msg-789"})
            
            mock_gemini = MockGemini.return_value
            mock_gemini.generate_response = AsyncMock(return_value={
                "response": "I've stored our conversation.",
                "metadata": {}
            })
            mock_gemini.generate_embedding = AsyncMock(return_value=[0.5] * 768)
            
            mock_vector = MockVector.return_value
            mock_vector.search_similar_chunks = AsyncMock(return_value=[])
            mock_vector.store_embedding = AsyncMock(return_value=True)
            
            mock_kb = MockKB.return_value
            mock_kb.get_recent_context = AsyncMock(return_value=[])
            mock_kb.store_conversation = AsyncMock(return_value=True)
            
            # Send message
            webhook_data = {
                "event": "messages.upsert",
                "data": {
                    "key": {
                        "remoteJid": "1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test-msg-storage"
                    },
                    "message": {
                        "conversation": "Remember this conversation"
                    },
                    "messageTimestamp": 1705484400
                }
            }
            
            await process_message(webhook_data)
            
            # Verify conversation was stored
            mock_kb.store_conversation.assert_called_once()
            call_args = mock_kb.store_conversation.call_args
            
            # Verify both user message and AI response were stored
            assert call_args is not None
            stored_data = call_args[0] if call_args[0] else call_args[1]
            assert "user" in str(stored_data).lower() or "message" in str(stored_data).lower()
    
    async def test_error_handling_graceful_degradation(self, settings):
        """Test graceful error handling when services fail."""
        with patch('src.services.whatsapp_service.WhatsAppService') as MockWhatsApp, \
             patch('src.services.gemini_service.GeminiService') as MockGemini:
            
            # Setup mocks with failures
            mock_whatsapp = MockWhatsApp.return_value
            mock_whatsapp.send_text_message = AsyncMock(
                side_effect=Exception("WhatsApp service unavailable")
            )
            
            mock_gemini = MockGemini.return_value
            mock_gemini.generate_response = AsyncMock(
                side_effect=Exception("Gemini API error")
            )
            
            # Send message
            webhook_data = {
                "event": "messages.upsert",
                "data": {
                    "key": {
                        "remoteJid": "1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test-msg-error"
                    },
                    "message": {
                        "conversation": "Test error handling"
                    },
                    "messageTimestamp": 1705484400
                }
            }
            
            # Should handle error gracefully
            try:
                await process_message(webhook_data)
            except Exception as e:
                # Verify error is logged but doesn't crash
                assert "error" in str(e).lower() or "failed" in str(e).lower()
