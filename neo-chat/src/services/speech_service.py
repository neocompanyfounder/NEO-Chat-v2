"""Speech-to-Text service using Google Cloud Speech API (T076-T079).

This module provides voice message transcription capabilities using Google Cloud
Speech-to-Text API with support for multiple audio formats and languages.
"""

import base64
import httpx
from typing import Dict, Any, Optional
from enum import Enum
from src.utils.config import Settings
from src.utils.logger import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


class AudioFormat(str, Enum):
    """Supported audio formats for transcription."""
    OGG = "ogg"
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    AAC = "aac"


class SpeechLanguage(str, Enum):
    """Supported languages for transcription."""
    ENGLISH_US = "en-US"
    SPANISH_ES = "es-ES"
    FRENCH_FR = "fr-FR"
    GERMAN_DE = "de-DE"
    PORTUGUESE_BR = "pt-BR"
    ITALIAN_IT = "it-IT"
    DUTCH_NL = "nl-NL"
    RUSSIAN_RU = "ru-RU"
    JAPANESE_JA = "ja-JP"
    KOREAN_KO = "ko-KR"
    CHINESE_CN = "zh-CN"
    ARABIC_SA = "ar-SA"


class SpeechServiceError(Exception):
    """Exception raised for speech service errors."""
    pass


class SpeechService:
    """Service for speech-to-text transcription using Google Cloud Speech API."""
    
    # Audio format to encoding mapping
    FORMAT_ENCODING_MAP = {
        AudioFormat.OGG: "OGG_OPUS",
        AudioFormat.MP3: "MP3",
        AudioFormat.WAV: "LINEAR16",
        AudioFormat.M4A: "MP3",  # M4A often uses AAC, but MP3 works for most
        AudioFormat.AAC: "MP3"
    }
    
    # Maximum audio duration (60 seconds)
    MAX_DURATION_SECONDS = 60
    
    # Minimum confidence threshold (85%)
    MIN_CONFIDENCE_THRESHOLD = 0.85
    
    def __init__(self, settings: Settings):
        """Initialize speech service.
        
        Args:
            settings: Application settings
            
        Raises:
            SpeechServiceError: If API key is not configured
        """
        self.settings = settings
        self.api_key = settings.GOOGLE_API_KEY
        
        if not self.api_key:
            raise SpeechServiceError("Google API key not configured")
        
        self.api_url = "https://speech.googleapis.com/v1/speech:recognize"
        
        logger.info("Speech service initialized")
    
    def detect_audio_format(self, filename: str, mime_type: str) -> AudioFormat:
        """Detect audio format from filename and MIME type (T077).
        
        Args:
            filename: Audio file name
            mime_type: MIME type
            
        Returns:
            Detected audio format
            
        Raises:
            SpeechServiceError: If format is not supported
        """
        # Check by extension first
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.ogg'):
            return AudioFormat.OGG
        elif filename_lower.endswith('.mp3'):
            return AudioFormat.MP3
        elif filename_lower.endswith('.wav'):
            return AudioFormat.WAV
        elif filename_lower.endswith('.m4a'):
            return AudioFormat.M4A
        elif filename_lower.endswith('.aac'):
            return AudioFormat.AAC
        
        # Check by MIME type
        mime_lower = mime_type.lower()
        
        if 'ogg' in mime_lower or 'opus' in mime_lower:
            return AudioFormat.OGG
        elif 'mp3' in mime_lower or 'mpeg' in mime_lower:
            return AudioFormat.MP3
        elif 'wav' in mime_lower or 'wave' in mime_lower:
            return AudioFormat.WAV
        elif 'm4a' in mime_lower:
            return AudioFormat.M4A
        elif 'aac' in mime_lower:
            return AudioFormat.AAC
        
        raise SpeechServiceError(
            f"Unsupported audio format: {filename} ({mime_type}). "
            f"Supported formats: OGG, MP3, WAV, M4A, AAC"
        )
    
    def validate_audio_duration(self, duration_seconds: Optional[float]) -> bool:
        """Validate audio duration (T077).
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            True if duration is valid
            
        Raises:
            SpeechServiceError: If duration exceeds limit
        """
        if duration_seconds is None:
            # If duration unknown, allow it (will be checked by API)
            return True
        
        if duration_seconds > self.MAX_DURATION_SECONDS:
            raise SpeechServiceError(
                f"Audio duration {duration_seconds:.1f}s exceeds maximum "
                f"allowed duration of {self.MAX_DURATION_SECONDS}s"
            )
        
        return True
    
    def detect_language(self, language_hint: Optional[str] = None) -> SpeechLanguage:
        """Detect or select language for transcription (T078).
        
        Args:
            language_hint: Optional language hint (e.g., "en", "es")
            
        Returns:
            Language code for transcription
        """
        if not language_hint:
            return SpeechLanguage.ENGLISH_US
        
        # Map common language codes to full codes
        language_map = {
            "en": SpeechLanguage.ENGLISH_US,
            "es": SpeechLanguage.SPANISH_ES,
            "fr": SpeechLanguage.FRENCH_FR,
            "de": SpeechLanguage.GERMAN_DE,
            "pt": SpeechLanguage.PORTUGUESE_BR,
            "it": SpeechLanguage.ITALIAN_IT,
            "nl": SpeechLanguage.DUTCH_NL,
            "ru": SpeechLanguage.RUSSIAN_RU,
            "ja": SpeechLanguage.JAPANESE_JA,
            "ko": SpeechLanguage.KOREAN_KO,
            "zh": SpeechLanguage.CHINESE_CN,
            "ar": SpeechLanguage.ARABIC_SA
        }
        
        hint_lower = language_hint.lower()[:2]
        return language_map.get(hint_lower, SpeechLanguage.ENGLISH_US)
    
    def validate_confidence(self, confidence: float) -> tuple[bool, str]:
        """Validate transcription confidence (T079).
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        if confidence >= self.MIN_CONFIDENCE_THRESHOLD:
            return True, ""
        
        warning = (
            f"Low transcription confidence: {confidence:.1%}. "
            f"The transcription may not be accurate."
        )
        
        return False, warning
    
    @with_retry(max_attempts=3, backoff_base=1)
    async def transcribe_audio(
        self,
        audio_content: bytes,
        filename: str,
        mime_type: str = "audio/ogg",
        language_hint: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """Transcribe audio to text using Google Cloud Speech-to-Text (T076).
        
        Args:
            audio_content: Raw audio bytes
            filename: Audio file name
            mime_type: MIME type of audio
            language_hint: Optional language hint
            duration_seconds: Optional audio duration
            
        Returns:
            Dictionary with transcription results:
            {
                "success": bool,
                "text": str,
                "confidence": float,
                "language": str,
                "metadata": dict
            }
            
        Raises:
            SpeechServiceError: If transcription fails
        """
        logger.info(
            "Transcribing audio",
            extra={
                "filename": filename,
                "mime_type": mime_type,
                "size": len(audio_content)
            }
        )
        
        try:
            # Validate audio
            if not audio_content:
                raise SpeechServiceError("Empty audio content")
            
            # Detect format
            audio_format = self.detect_audio_format(filename, mime_type)
            encoding = self.FORMAT_ENCODING_MAP[audio_format]
            
            # Validate duration
            self.validate_audio_duration(duration_seconds)
            
            # Detect language
            language = self.detect_language(language_hint)
            
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            
            # Prepare request
            request_data = {
                "config": {
                    "encoding": encoding,
                    "languageCode": language.value,
                    "enableAutomaticPunctuation": True,
                    "model": "default",
                    "useEnhanced": True
                },
                "audio": {
                    "content": audio_base64
                }
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise SpeechServiceError(f"API error: {error_msg}")
                
                result = response.json()
            
            # Extract transcription
            if "results" not in result or not result["results"]:
                raise SpeechServiceError("No transcription results returned")
            
            # Get best alternative
            alternatives = result["results"][0].get("alternatives", [])
            if not alternatives:
                raise SpeechServiceError("No transcription alternatives found")
            
            best_alternative = alternatives[0]
            transcript = best_alternative.get("transcript", "")
            confidence = best_alternative.get("confidence", 0.0)
            
            if not transcript:
                raise SpeechServiceError("Empty transcription result")
            
            # Validate confidence
            is_confident, warning = self.validate_confidence(confidence)
            
            logger.info(
                "Audio transcribed successfully",
                extra={
                    "filename": filename,
                    "text_length": len(transcript),
                    "confidence": confidence,
                    "language": language.value
                }
            )
            
            return {
                "success": True,
                "text": transcript,
                "confidence": confidence,
                "language": language.value,
                "is_confident": is_confident,
                "warning": warning if not is_confident else None,
                "metadata": {
                    "filename": filename,
                    "format": audio_format.value,
                    "encoding": encoding,
                    "duration_seconds": duration_seconds,
                    "alternatives_count": len(alternatives)
                }
            }
            
        except SpeechServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to transcribe audio: {str(e)}",
                extra={
                    "filename": filename,
                    "error": str(e)
                }
            )
            raise SpeechServiceError(f"Transcription failed: {str(e)}")
    
    async def transcribe_audio_with_alternatives(
        self,
        audio_content: bytes,
        filename: str,
        mime_type: str = "audio/ogg",
        max_alternatives: int = 3
    ) -> Dict[str, Any]:
        """Transcribe audio with multiple alternatives.
        
        Args:
            audio_content: Raw audio bytes
            filename: Audio file name
            mime_type: MIME type
            max_alternatives: Maximum number of alternatives to return
            
        Returns:
            Dictionary with transcription and alternatives
        """
        result = await self.transcribe_audio(
            audio_content,
            filename,
            mime_type
        )
        
        # For now, just return the main result
        # In production, you could request multiple alternatives from the API
        result["alternatives"] = [
            {
                "text": result["text"],
                "confidence": result["confidence"]
            }
        ]
        
        return result
