"""Integration tests for Google Cloud Vision OCR service (T061)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.vision_service import VisionService, VisionServiceError
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        GOOGLE_API_KEY="test-api-key-for-vision"
    )


@pytest.fixture
def vision_service(settings):
    """Create vision service instance."""
    return VisionService(settings)


class TestVisionServiceInitialization:
    """Test vision service initialization."""
    
    def test_init_with_api_key(self, settings):
        """Test initialization with API key."""
        service = VisionService(settings)
        assert service.api_key == "test-api-key-for-vision"
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        settings = Settings(GOOGLE_API_KEY="")
        
        with pytest.raises(VisionServiceError) as exc_info:
            VisionService(settings)
        
        assert "API key" in str(exc_info.value)


class TestTextDetection:
    """Test text detection from images."""
    
    @pytest.mark.asyncio
    async def test_extract_text_from_image_success(self, vision_service):
        """Test successful text extraction from image."""
        mock_image_content = b"fake_image_data"
        
        # Mock the Vision API response
        mock_response = {
            "responses": [{
                "textAnnotations": [
                    {"description": "Hello World\nThis is a test image"},
                    {"description": "Hello"},
                    {"description": "World"}
                ],
                "fullTextAnnotation": {
                    "text": "Hello World\nThis is a test image"
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_image(
                mock_image_content,
                "test.jpg"
            )
            
            assert result["success"] is True
            assert "Hello World" in result["text"]
            assert "test image" in result["text"]
            assert result["metadata"]["confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_extract_text_no_text_found(self, vision_service):
        """Test image with no text."""
        mock_image_content = b"fake_image_data"
        
        # Mock empty response
        mock_response = {
            "responses": [{}]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            with pytest.raises(VisionServiceError) as exc_info:
                await vision_service.extract_text_from_image(
                    mock_image_content,
                    "test.jpg"
                )
            
            assert "No text found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_text_api_error(self, vision_service):
        """Test handling of API errors."""
        mock_image_content = b"fake_image_data"
        
        # Mock error response
        mock_response = {
            "responses": [{
                "error": {
                    "code": 400,
                    "message": "Invalid image"
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            with pytest.raises(VisionServiceError) as exc_info:
                await vision_service.extract_text_from_image(
                    mock_image_content,
                    "test.jpg"
                )
            
            assert "Invalid image" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_text_network_error(self, vision_service):
        """Test handling of network errors."""
        mock_image_content = b"fake_image_data"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Network timeout")
            
            with pytest.raises(VisionServiceError) as exc_info:
                await vision_service.extract_text_from_image(
                    mock_image_content,
                    "test.jpg"
                )
            
            assert "Failed to extract" in str(exc_info.value)


class TestDocumentTextDetection:
    """Test document text detection (for scanned documents)."""
    
    @pytest.mark.asyncio
    async def test_extract_text_from_document_success(self, vision_service):
        """Test successful document text extraction."""
        mock_image_content = b"fake_document_image"
        
        # Mock document text detection response
        mock_response = {
            "responses": [{
                "fullTextAnnotation": {
                    "text": "This is a scanned document.\nWith multiple lines.\nAnd paragraphs.",
                    "pages": [{
                        "width": 1000,
                        "height": 1400,
                        "blocks": [
                            {"confidence": 0.95},
                            {"confidence": 0.92}
                        ]
                    }]
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_document(
                mock_image_content,
                "document.jpg"
            )
            
            assert result["success"] is True
            assert "scanned document" in result["text"]
            assert result["metadata"]["pages"] == 1
            assert result["metadata"]["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_extract_text_from_document_low_confidence(self, vision_service):
        """Test document with low confidence text."""
        mock_image_content = b"fake_document_image"
        
        # Mock low confidence response
        mock_response = {
            "responses": [{
                "fullTextAnnotation": {
                    "text": "Blurry text",
                    "pages": [{
                        "blocks": [
                            {"confidence": 0.3},
                            {"confidence": 0.4}
                        ]
                    }]
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_document(
                mock_image_content,
                "blurry.jpg"
            )
            
            # Should still succeed but with low confidence
            assert result["success"] is True
            assert result["metadata"]["confidence"] < 0.5


class TestImageValidation:
    """Test image validation and preprocessing."""
    
    @pytest.mark.asyncio
    async def test_extract_text_empty_image(self, vision_service):
        """Test handling of empty image data."""
        with pytest.raises(VisionServiceError) as exc_info:
            await vision_service.extract_text_from_image(b"", "test.jpg")
        
        assert "empty" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_extract_text_large_image(self, vision_service):
        """Test handling of large images."""
        # Create fake large image (20MB)
        large_image = b"x" * (20 * 1024 * 1024)
        
        # Mock successful response (API should handle large images)
        mock_response = {
            "responses": [{
                "textAnnotations": [
                    {"description": "Text from large image"}
                ]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_image(
                large_image,
                "large.jpg"
            )
            
            assert result["success"] is True


class TestRetryLogic:
    """Test retry logic for transient failures."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, vision_service):
        """Test that service retries on transient errors."""
        mock_image_content = b"fake_image_data"
        
        # Mock responses: first fails, second succeeds
        call_count = 0
        
        def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            response = AsyncMock()
            if call_count == 1:
                # First call fails
                response.status_code = 503
                response.json = Mock(return_value={"error": "Service unavailable"})
            else:
                # Second call succeeds
                response.status_code = 200
                response.json = Mock(return_value={
                    "responses": [{
                        "textAnnotations": [
                            {"description": "Success after retry"}
                        ]
                    }]
                })
            
            return response
        
        with patch('httpx.AsyncClient.post', side_effect=mock_post_side_effect):
            result = await vision_service.extract_text_from_image(
                mock_image_content,
                "test.jpg"
            )
            
            # Should succeed after retry
            assert result["success"] is True
            assert call_count > 1  # Verify retry happened
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, vision_service):
        """Test that service fails after max retries."""
        mock_image_content = b"fake_image_data"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Always return error
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 503
            mock_post.return_value.json = Mock(return_value={"error": "Service unavailable"})
            
            with pytest.raises(VisionServiceError):
                await vision_service.extract_text_from_image(
                    mock_image_content,
                    "test.jpg"
                )


class TestMultiLanguageSupport:
    """Test multi-language text detection."""
    
    @pytest.mark.asyncio
    async def test_extract_text_multilingual(self, vision_service):
        """Test extraction of multilingual text."""
        mock_image_content = b"fake_image_data"
        
        # Mock multilingual response
        mock_response = {
            "responses": [{
                "textAnnotations": [
                    {"description": "Hello 世界 Bonjour مرحبا"}
                ],
                "fullTextAnnotation": {
                    "text": "Hello 世界 Bonjour مرحبا"
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_image(
                mock_image_content,
                "multilingual.jpg"
            )
            
            assert result["success"] is True
            assert "Hello" in result["text"]
            assert "世界" in result["text"]
            assert "Bonjour" in result["text"]


class TestMetadataExtraction:
    """Test metadata extraction from OCR results."""
    
    @pytest.mark.asyncio
    async def test_metadata_includes_confidence(self, vision_service):
        """Test that metadata includes confidence scores."""
        mock_image_content = b"fake_image_data"
        
        mock_response = {
            "responses": [{
                "textAnnotations": [
                    {"description": "Test text", "confidence": 0.95}
                ]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_image(
                mock_image_content,
                "test.jpg"
            )
            
            assert "confidence" in result["metadata"]
            assert 0 <= result["metadata"]["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_metadata_includes_filename(self, vision_service):
        """Test that metadata includes filename."""
        mock_image_content = b"fake_image_data"
        
        mock_response = {
            "responses": [{
                "textAnnotations": [
                    {"description": "Test"}
                ]
            }]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = Mock(return_value=mock_response)
            
            result = await vision_service.extract_text_from_image(
                mock_image_content,
                "my_image.jpg"
            )
            
            assert result["metadata"]["filename"] == "my_image.jpg"


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_extract_text_timeout(self, vision_service):
        """Test that requests timeout appropriately."""
        mock_image_content = b"fake_image_data"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate timeout
            import asyncio
            
            async def slow_request(*args, **kwargs):
                await asyncio.sleep(100)  # Very slow
                return AsyncMock()
            
            mock_post.side_effect = slow_request
            
            with pytest.raises(VisionServiceError):
                await vision_service.extract_text_from_image(
                    mock_image_content,
                    "test.jpg"
                )
