"""Google Cloud Vision service for OCR on images.

This module provides OCR capabilities using Google Cloud Vision API
for extracting text from images.
"""

import base64
from typing import Dict, Any, Optional
from src.utils.config import Settings
from src.utils.logger import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


class VisionServiceError(Exception):
    """Exception raised for Vision API errors."""
    pass


class VisionService:
    """Service for OCR using Google Cloud Vision API."""
    
    def __init__(self, settings: Settings):
        """Initialize Vision service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_key = settings.GOOGLE_API_KEY
        
        # Initialize Google Cloud Vision client
        try:
            from google.cloud import vision
            self.client = vision.ImageAnnotatorClient()
            logger.info("Vision service initialized")
        except ImportError:
            logger.warning("google-cloud-vision not installed, OCR will not be available")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Vision client: {str(e)}")
            self.client = None
    
    @with_retry(max_attempts=3, backoff_base=1)
    async def extract_text_from_image(
        self,
        image_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Extract text from an image using OCR.
        
        Args:
            image_content: Image file bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted text and metadata
            
        Raises:
            VisionServiceError: If OCR fails
        """
        if self.client is None:
            raise VisionServiceError("Vision client not initialized")
        
        try:
            from google.cloud import vision
            
            # Create image object
            image = vision.Image(content=image_content)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise VisionServiceError(
                    f"Vision API error: {response.error.message}"
                )
            
            # Extract full text
            texts = response.text_annotations
            
            if not texts:
                logger.warning(
                    f"No text detected in image: {filename}",
                    extra={"filename": filename}
                )
                return {
                    "text": "",
                    "metadata": {
                        "format": "image",
                        "text_detected": False
                    }
                }
            
            # First annotation contains the full text
            full_text = texts[0].description
            
            # Extract metadata
            metadata = {
                "format": "image",
                "text_detected": True,
                "text_blocks": len(texts) - 1,  # Excluding the first full text annotation
                "confidence": self._calculate_confidence(texts)
            }
            
            logger.info(
                f"Extracted text from image: {len(full_text)} characters",
                extra={
                    "filename": filename,
                    "text_length": len(full_text),
                    "text_blocks": metadata["text_blocks"],
                    "confidence": metadata["confidence"]
                }
            )
            
            return {
                "text": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(
                f"Failed to extract text from image: {str(e)}",
                extra={
                    "filename": filename,
                    "error": str(e)
                }
            )
            raise VisionServiceError(f"OCR failed: {str(e)}")
    
    def _calculate_confidence(self, text_annotations) -> float:
        """Calculate average confidence score from text annotations.
        
        Args:
            text_annotations: List of text annotations from Vision API
            
        Returns:
            Average confidence score (0.0 to 1.0)
        """
        if len(text_annotations) <= 1:
            return 1.0
        
        # Skip the first annotation (full text) and calculate average
        confidences = []
        for annotation in text_annotations[1:]:
            if hasattr(annotation, 'confidence'):
                confidences.append(annotation.confidence)
        
        if not confidences:
            return 1.0
        
        return sum(confidences) / len(confidences)
    
    async def detect_document_text(
        self,
        image_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Detect text in documents with better formatting preservation.
        
        This method is optimized for documents and preserves layout better
        than the standard text detection.
        
        Args:
            image_content: Image file bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted text and metadata
            
        Raises:
            VisionServiceError: If OCR fails
        """
        if self.client is None:
            raise VisionServiceError("Vision client not initialized")
        
        try:
            from google.cloud import vision
            
            # Create image object
            image = vision.Image(content=image_content)
            
            # Perform document text detection
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                raise VisionServiceError(
                    f"Vision API error: {response.error.message}"
                )
            
            if not response.full_text_annotation:
                logger.warning(
                    f"No text detected in document: {filename}",
                    extra={"filename": filename}
                )
                return {
                    "text": "",
                    "metadata": {
                        "format": "document_image",
                        "text_detected": False
                    }
                }
            
            # Extract text with page structure
            full_text = response.full_text_annotation.text
            
            # Extract metadata
            metadata = {
                "format": "document_image",
                "text_detected": True,
                "pages": len(response.full_text_annotation.pages),
                "language": self._detect_language(response.full_text_annotation)
            }
            
            logger.info(
                f"Extracted document text: {len(full_text)} characters",
                extra={
                    "filename": filename,
                    "text_length": len(full_text),
                    "pages": metadata["pages"],
                    "language": metadata["language"]
                }
            )
            
            return {
                "text": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(
                f"Failed to extract document text: {str(e)}",
                extra={
                    "filename": filename,
                    "error": str(e)
                }
            )
            raise VisionServiceError(f"Document OCR failed: {str(e)}")
    
    def _detect_language(self, text_annotation) -> Optional[str]:
        """Detect the primary language in the text.
        
        Args:
            text_annotation: Full text annotation from Vision API
            
        Returns:
            Language code or None
        """
        if not text_annotation.pages:
            return None
        
        # Get language from first page
        first_page = text_annotation.pages[0]
        if hasattr(first_page.property, 'detected_languages'):
            languages = first_page.property.detected_languages
            if languages:
                return languages[0].language_code
        
        return None
