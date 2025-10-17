"""Integration tests for Google Cloud Speech-to-Text service (T082)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.speech_service import (
    SpeechService,
    SpeechServiceError,
    AudioFormat,
    SpeechLanguage
)
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        GOOGLE_API_KEY="test-api-key-for-speech"
    )


@pytest.fixture
def speech_service(settings):
    """Create speech service instance."""
    return SpeechService(settings)


class TestSpeechServiceInitialization:
    """Test speech service initialization."""
    
    def test_init_with_api_key(self, settings):
        """Test initialization with API key."""
        service = SpeechService(settings)
        assert service.api_key == "test-api-key-for-speech"
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        settings = Settings(GOOGLE_API_KEY="")
        
        with pytest.raises(SpeechServiceError) as exc_info:
            SpeechService(settings)
        
        assert "API key" in str(exc_info.value)


class TestAudioFormatDetection:
    """Test audio format detection (T077)."""
    
    def test_detect_ogg_by_extension(self, speech_service):
        """Test OGG detection by file extension."""
        format = speech_service.detect_audio_format("voice.ogg", "audio/ogg")
        assert format == AudioFormat.OGG
    
    def test_detect_mp3_by_extension(self, speech_service):
        """Test MP3 detection by file extension."""
        format = speech_service.detect_audio_format("audio.mp3", "audio/mpeg")
        assert format == AudioFormat.MP3
    
    def test_detect_wav_by_extension(self, speech_service):
        """Test WAV detection by file extension."""
        format = speech_service.detect_audio_format("recording.wav", "audio/wav")
        assert format == AudioFormat.WAV
    
    def test_detect_m4a_by_extension(self, speech_service):
        """Test M4A detection by file extension."""
        format = speech_service.detect_audio_format("voice.m4a", "audio/m4a")
        assert format == AudioFormat.M4A
    
    def test_detect_by_mime_type(self, speech_service):
        """Test detection by MIME type when extension is unclear."""
        format = speech_service.detect_audio_format("audio", "audio/ogg; codecs=opus")
        assert format == AudioFormat.OGG
    
    def test_detect_unsupported_format(self, speech_service):
        """Test detection of unsupported format."""
        with pytest.raises(SpeechServiceError) as exc_info:
            speech_service.detect_audio_format("video.mp4", "video/mp4")
        
        assert "Unsupported audio format" in str(exc_info.value)


class TestDurationValidation:
    """Test audio duration validation (T077)."""
    
    def test_validate_valid_duration(self, speech_service):
        """Test validation of valid duration."""
        assert speech_service.validate_audio_duration(30.0) is True
    
    def test_validate_max_duration(self, speech_service):
        """Test validation at maximum duration."""
        assert speech_service.validate_audio_duration(60.0) is True
    
    def test_validate_exceeds_max_duration(self, speech_service):
        """Test validation when duration exceeds maximum."""
        with pytest.raises(SpeechServiceError) as exc_info:
            speech_service.validate_audio_duration(65.0)
        
        assert "exceeds maximum" in str(exc_info.value)
        assert "60" in str(exc_info.value)
    
    def test_validate_unknown_duration(self, speech_service):
        """Test validation when duration is unknown."""
        assert speech_service.validate_audio_duration(None) is True


class TestLanguageDetection:
    """Test language detection (T078)."""
    
    def test_detect_english(self, speech_service):
        """Test English language detection."""
        lang = speech_service.detect_language("en")
        assert lang == SpeechLanguage.ENGLISH_US
    
    def test_detect_spanish(self, speech_service):
        """Test Spanish language detection."""
        lang = speech_service.detect_language("es")
        assert lang == SpeechLanguage.SPANISH_ES
    
    def test_detect_french(self, speech_service):
        """Test French language detection."""
        lang = speech_service.detect_language("fr")
        assert lang == SpeechLanguage.FRENCH_FR
    
    def test_detect_german(self, speech_service):
        """Test German language detection."""
        lang = speech_service.detect_language("de")
        assert lang == SpeechLanguage.GERMAN_DE
    
    def test_detect_default_language(self, speech_service):
        """Test default language when no hint provided."""
        lang = speech_service.detect_language(None)
        assert lang == SpeechLanguage.ENGLISH_US
    
    def test_detect_unknown_language(self, speech_service):
        """Test unknown language defaults to English."""
        lang = speech_service.detect_language("xx")
        assert lang == SpeechLanguage.ENGLISH_US


class TestConfidenceValidation:
    """Test transcription confidence validation (T079)."""
    
    def test_validate_high_confidence(self, speech_service):
        """Test validation of high confidence."""
        is_valid, warning = speech_service.validate_confidence(0.95)
        assert is_valid is True
        assert warning == ""
    
    def test_validate_threshold_confidence(self, speech_service):
        """Test validation at threshold."""
        is_valid, warning = speech_service.validate_confidence(0.85)
        assert is_valid is True
        assert warning == ""
    
    def test_validate_low_confidence(self, speech_service):
        """Test validation of low confidence."""
        is_valid, warning = speech_service.validate_confidence(0.70)
        assert is_valid is False
        assert "Low transcription confidence" in warning
        assert "70" in warning


class TestTranscription:
    """Test audio transcription."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, speech_service):
        """Test successful audio transcription."""
        mock_audio = b"fake_audio_data"
        
        # Mock API response
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Hello, this is a test message.",
                    "confidence": 0.95
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.ogg",
                mime_type="audio/ogg"
            )
            
            assert result["success"] is True
            assert result["text"] == "Hello, this is a test message."
            assert result["confidence"] == 0.95
            assert result["is_confident"] is True
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_low_confidence(self, speech_service):
        """Test transcription with low confidence."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Unclear audio",
                    "confidence": 0.60
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.ogg",
                mime_type="audio/ogg"
            )
            
            assert result["success"] is True
            assert result["is_confident"] is False
            assert result["warning"] is not None
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_content(self, speech_service):
        """Test transcription with empty audio."""
        with pytest.raises(SpeechServiceError) as exc_info:
            await speech_service.transcribe_audio(
                audio_content=b"",
                filename="test.ogg",
                mime_type="audio/ogg"
            )
        
        assert "Empty audio" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, speech_service):
        """Test handling of API errors."""
        mock_audio = b"fake_audio_data"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 400
            mock_post.return_value.json = Mock(return_value={
                "error": {"message": "Invalid audio format"}
            })
            
            with pytest.raises(SpeechServiceError) as exc_info:
                await speech_service.transcribe_audio(
                    audio_content=mock_audio,
                    filename="test.ogg",
                    mime_type="audio/ogg"
                )
            
            assert "Invalid audio format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_results(self, speech_service):
        """Test handling when no transcription results."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {"results": []}
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            with pytest.raises(SpeechServiceError) as exc_info:
                await speech_service.transcribe_audio(
                    audio_content=mock_audio,
                    filename="test.ogg",
                    mime_type="audio/ogg"
                )
            
            assert "No transcription results" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_network_error(self, speech_service):
        """Test handling of network errors."""
        mock_audio = b"fake_audio_data"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Network timeout")
            
            with pytest.raises(SpeechServiceError) as exc_info:
                await speech_service.transcribe_audio(
                    audio_content=mock_audio,
                    filename="test.ogg",
                    mime_type="audio/ogg"
                )
            
            assert "Transcription failed" in str(exc_info.value)


class TestMultiLanguageTranscription:
    """Test multi-language transcription (T078)."""
    
    @pytest.mark.asyncio
    async def test_transcribe_spanish(self, speech_service):
        """Test Spanish transcription."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Hola, esto es una prueba.",
                    "confidence": 0.92
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.ogg",
                mime_type="audio/ogg",
                language_hint="es"
            )
            
            assert result["success"] is True
            assert result["language"] == "es-ES"
    
    @pytest.mark.asyncio
    async def test_transcribe_french(self, speech_service):
        """Test French transcription."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Bonjour, ceci est un test.",
                    "confidence": 0.90
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.ogg",
                mime_type="audio/ogg",
                language_hint="fr"
            )
            
            assert result["success"] is True
            assert result["language"] == "fr-FR"


class TestAudioFormats:
    """Test different audio formats."""
    
    @pytest.mark.asyncio
    async def test_transcribe_mp3(self, speech_service):
        """Test MP3 transcription."""
        mock_audio = b"fake_mp3_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "MP3 test",
                    "confidence": 0.88
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.mp3",
                mime_type="audio/mpeg"
            )
            
            assert result["success"] is True
            assert result["metadata"]["format"] == "mp3"
    
    @pytest.mark.asyncio
    async def test_transcribe_wav(self, speech_service):
        """Test WAV transcription."""
        mock_audio = b"fake_wav_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "WAV test",
                    "confidence": 0.91
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.wav",
                mime_type="audio/wav"
            )
            
            assert result["success"] is True
            assert result["metadata"]["format"] == "wav"


class TestMetadata:
    """Test metadata extraction."""
    
    @pytest.mark.asyncio
    async def test_metadata_includes_filename(self, speech_service):
        """Test that metadata includes filename."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Test",
                    "confidence": 0.90
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="my_voice.ogg",
                mime_type="audio/ogg"
            )
            
            assert result["metadata"]["filename"] == "my_voice.ogg"
    
    @pytest.mark.asyncio
    async def test_metadata_includes_duration(self, speech_service):
        """Test that metadata includes duration."""
        mock_audio = b"fake_audio_data"
        
        mock_response = {
            "results": [{
                "alternatives": [{
                    "transcript": "Test",
                    "confidence": 0.90
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await speech_service.transcribe_audio(
                audio_content=mock_audio,
                filename="test.ogg",
                mime_type="audio/ogg",
                duration_seconds=15.5
            )
            
            assert result["metadata"]["duration_seconds"] == 15.5
