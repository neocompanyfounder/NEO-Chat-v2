"""End-to-end tests for voice message journey (T083, T084)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.crew_manager import CrewManager
from src.agents.tool_agent import ToolAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.response_agent import ResponseAgent
from src.services.speech_service import SpeechService
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
        EVOLUTION_INSTANCE_NAME="test-instance"
    )


@pytest.fixture
def mock_whatsapp_service():
    """Create mock WhatsApp service."""
    service = AsyncMock(spec=WhatsAppService)
    service.send_text_message = AsyncMock()
    service.download_media = AsyncMock(return_value=b"fake_audio_content")
    return service


@pytest.fixture
def mock_knowledge_base_service():
    """Create mock knowledge base service."""
    service = AsyncMock(spec=KnowledgeBaseService)
    service.search = AsyncMock(return_value=[])
    service.store_conversation = AsyncMock()
    return service


@pytest.fixture
def mock_speech_service():
    """Create mock speech service."""
    service = AsyncMock(spec=SpeechService)
    service.transcribe_audio = AsyncMock(return_value={
        "success": True,
        "text": "Hello, what is the weather today?",
        "confidence": 0.95,
        "language": "en-US",
        "is_confident": True,
        "warning": None,
        "metadata": {
            "filename": "voice.ogg",
            "format": "ogg",
            "duration_seconds": 3.5
        }
    })
    return service


@pytest.fixture
def mock_retrieval_agent(mock_knowledge_base_service):
    """Create mock retrieval agent."""
    agent = AsyncMock(spec=RetrievalAgent)
    agent.search_knowledge_base = AsyncMock(return_value=[])
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def mock_response_agent():
    """Create mock response agent."""
    agent = AsyncMock(spec=ResponseAgent)
    agent.generate_response = AsyncMock(
        return_value="The weather today is sunny with a high of 75°F."
    )
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def tool_agent(
    mock_knowledge_base_service,
    mock_whatsapp_service,
    mock_speech_service
):
    """Create tool agent with mocked services."""
    agent = ToolAgent(
        knowledge_base_service=mock_knowledge_base_service,
        whatsapp_service=mock_whatsapp_service,
        speech_service=mock_speech_service
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


class TestVoiceMessageE2E:
    """End-to-end tests for voice message user journey."""
    
    @pytest.mark.asyncio
    async def test_complete_voice_message_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test complete journey: Send voice → Transcribe → AI Response (T084).
        
        This is the main E2E test for User Story 4.
        """
        user_id = "test-user-123"
        phone_number = "+1234567890"
        
        # Step 1: User sends voice message
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg; codecs=opus",
                "seconds": 3.5
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id=user_id,
            phone_number=phone_number,
            media_info=media_info
        )
        
        # Verify transcription was successful
        assert result["success"] is True
        assert result["text"] == "Hello, what is the weather today?"
        assert result["confidence"] == 0.95
        
        # Verify processing notification was sent
        assert mock_whatsapp_service.send_text_message.call_count >= 1
        first_call = mock_whatsapp_service.send_text_message.call_args_list[0]
        assert "Transcribing" in first_call[1]["message"]
        
        # Verify transcription was sent to user
        second_call = mock_whatsapp_service.send_text_message.call_args_list[1]
        assert "Transcription" in second_call[1]["message"]
        assert "Hello, what is the weather today?" in second_call[1]["message"]
        
        # Verify AI response was sent
        # (The process_simple_message is called after transcription)
        assert mock_whatsapp_service.send_text_message.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_voice_message_low_confidence(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test voice message with low confidence transcription."""
        # Mock low confidence transcription
        mock_speech_service.transcribe_audio = AsyncMock(return_value={
            "success": True,
            "text": "Unclear audio message",
            "confidence": 0.65,
            "language": "en-US",
            "is_confident": False,
            "warning": "Low transcription confidence: 65%. The transcription may not be accurate.",
            "metadata": {}
        })
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 5.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        # Verify success despite low confidence
        assert result["success"] is True
        
        # Verify warning was included in transcription message
        transcription_msg = mock_whatsapp_service.send_text_message.call_args_list[1][1]["message"]
        assert "Low confidence" in transcription_msg or "65%" in transcription_msg
    
    @pytest.mark.asyncio
    async def test_voice_message_transcription_failure(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test handling of transcription failures."""
        # Mock transcription failure
        mock_speech_service.transcribe_audio = AsyncMock(return_value={
            "success": False,
            "error": "Audio too noisy to transcribe"
        })
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 2.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        # Verify failure
        assert result["success"] is False
        
        # Verify error notification
        error_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "Failed to transcribe" in error_msg
    
    @pytest.mark.asyncio
    async def test_voice_message_download_failure(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test handling of media download failures."""
        # Mock download failure
        mock_whatsapp_service.download_media = AsyncMock(return_value=None)
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 3.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_voice_message_different_languages(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test voice messages in different languages."""
        # Mock Spanish transcription
        mock_speech_service.transcribe_audio = AsyncMock(return_value={
            "success": True,
            "text": "Hola, ¿cómo estás?",
            "confidence": 0.92,
            "language": "es-ES",
            "is_confident": True,
            "warning": None,
            "metadata": {}
        })
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice_es.ogg",
                "mimetype": "audio/ogg",
                "seconds": 2.5
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is True
        assert "Hola" in result["text"]
    
    @pytest.mark.asyncio
    async def test_voice_message_duration_limit(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test voice message exceeding duration limit."""
        # Mock duration error
        from src.services.speech_service import SpeechServiceError
        mock_speech_service.transcribe_audio = AsyncMock(
            side_effect=SpeechServiceError("Audio duration 65.0s exceeds maximum allowed duration of 60s")
        )
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/long_voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 65.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is False
        assert "60" in result["error"] or "duration" in result["error"].lower()


class TestVoiceMessageFormats:
    """Test different voice message formats."""
    
    @pytest.mark.asyncio
    async def test_voice_message_mp3(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test MP3 voice message."""
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.mp3",
                "mimetype": "audio/mpeg",
                "seconds": 4.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_voice_message_wav(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test WAV voice message."""
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.wav",
                "mimetype": "audio/wav",
                "seconds": 3.0
            },
            "is_voice": True
        }
        
        result = await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is True


class TestVoiceMessageIntegration:
    """Integration tests for voice message components."""
    
    @pytest.mark.asyncio
    async def test_tool_agent_voice_processing(
        self,
        tool_agent,
        mock_speech_service
    ):
        """Test tool agent voice message processing."""
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 3.0
            },
            "is_voice": True
        }
        
        result = await tool_agent.process_voice_message(
            user_id="test-user",
            media_info=media_info
        )
        
        assert result["success"] is True
        assert "text" in result
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_tool_agent_without_speech_service(
        self,
        mock_knowledge_base_service,
        mock_whatsapp_service
    ):
        """Test tool agent when speech service not available."""
        agent = ToolAgent(
            knowledge_base_service=mock_knowledge_base_service,
            whatsapp_service=mock_whatsapp_service,
            speech_service=None  # No speech service
        )
        
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg"
            },
            "is_voice": True
        }
        
        result = await agent.process_voice_message(
            user_id="test-user",
            media_info=media_info
        )
        
        assert result["success"] is False
        assert "not available" in result["error"].lower()


class TestVoiceMessageConversationFlow:
    """Test voice message integration with conversation flow."""
    
    @pytest.mark.asyncio
    async def test_voice_message_stored_in_history(
        self,
        crew_manager,
        mock_knowledge_base_service,
        mock_whatsapp_service
    ):
        """Test that transcribed voice is stored in conversation history."""
        media_info = {
            "type": "audioMessage",
            "data": {
                "url": "https://example.com/voice.ogg",
                "mimetype": "audio/ogg",
                "seconds": 3.0
            },
            "is_voice": True
        }
        
        await crew_manager.process_voice_message(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        # Verify conversation was stored
        # (This happens in process_simple_message which is called after transcription)
        assert mock_knowledge_base_service.store_conversation.called
    
    @pytest.mark.asyncio
    async def test_sequential_voice_messages(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_speech_service
    ):
        """Test processing multiple voice messages in sequence."""
        messages = [
            ("First voice message", 0.90),
            ("Second voice message", 0.92),
            ("Third voice message", 0.88)
        ]
        
        results = []
        for text, confidence in messages:
            # Mock different transcriptions
            mock_speech_service.transcribe_audio = AsyncMock(return_value={
                "success": True,
                "text": text,
                "confidence": confidence,
                "language": "en-US",
                "is_confident": True,
                "warning": None,
                "metadata": {}
            })
            
            media_info = {
                "type": "audioMessage",
                "data": {
                    "url": f"https://example.com/{text.replace(' ', '_')}.ogg",
                    "mimetype": "audio/ogg",
                    "seconds": 3.0
                },
                "is_voice": True
            }
            
            result = await crew_manager.process_voice_message(
                user_id="test-user",
                phone_number="+1234567890",
                media_info=media_info
            )
            results.append(result)
        
        # All should succeed
        assert all(r["success"] for r in results)
        assert len(results) == 3
