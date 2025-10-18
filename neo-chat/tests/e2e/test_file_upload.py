"""End-to-end tests for file upload journey (T062, T063)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.crew_manager import CrewManager
from src.agents.tool_agent import ToolAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.response_agent import ResponseAgent
from src.services.rag_ingestion_service import RAGIngestionService
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
    service.download_media = AsyncMock(return_value=b"fake_file_content")
    return service


@pytest.fixture
def mock_knowledge_base_service():
    """Create mock knowledge base service."""
    service = AsyncMock(spec=KnowledgeBaseService)
    service.search = AsyncMock(return_value=[
        {
            "text": "Information from uploaded document",
            "metadata": {"filename": "test.pdf", "page": 1}
        }
    ])
    service.store_conversation = AsyncMock()
    return service


@pytest.fixture
def mock_rag_ingestion_service():
    """Create mock RAG ingestion service."""
    service = AsyncMock(spec=RAGIngestionService)
    service.ingest_document = AsyncMock(return_value={
        "success": True,
        "document_id": "doc-123",
        "chunks_created": 5,
        "filename": "test.pdf"
    })
    return service


@pytest.fixture
def mock_retrieval_agent(mock_knowledge_base_service):
    """Create mock retrieval agent."""
    agent = AsyncMock(spec=RetrievalAgent)
    agent.search_knowledge_base = AsyncMock(return_value=[
        {
            "text": "Information from uploaded document",
            "metadata": {"filename": "test.pdf"}
        }
    ])
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def mock_response_agent():
    """Create mock response agent."""
    agent = AsyncMock(spec=ResponseAgent)
    agent.generate_response = AsyncMock(
        return_value="Based on the uploaded document, here's the answer..."
    )
    agent.get_agent = Mock()
    return agent


@pytest.fixture
def tool_agent(
    mock_knowledge_base_service,
    mock_whatsapp_service,
    mock_rag_ingestion_service
):
    """Create tool agent with mocked services."""
    agent = ToolAgent(
        knowledge_base_service=mock_knowledge_base_service,
        whatsapp_service=mock_whatsapp_service,
        rag_ingestion_service=mock_rag_ingestion_service
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


class TestFileUploadE2E:
    """End-to-end tests for file upload user journey."""
    
    @pytest.mark.asyncio
    async def test_complete_pdf_upload_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test complete journey: Upload PDF → Process → Query → Response (T063).
        
        This is the main E2E test for User Story 2.
        """
        user_id = "test-user-123"
        phone_number = "+1234567890"
        
        # Step 1: User uploads PDF file
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/document.pdf",
                "mimetype": "application/pdf",
                "fileName": "test_document.pdf"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id=user_id,
            phone_number=phone_number,
            media_info=media_info,
            caption="This is my document"
        )
        
        # Verify file was processed
        assert result["success"] is True
        assert result["document_id"] == "doc-123"
        assert result["chunks_created"] == 5
        
        # Verify processing notification was sent
        assert mock_whatsapp_service.send_text_message.call_count >= 1
        first_call = mock_whatsapp_service.send_text_message.call_args_list[0]
        assert "Processing" in first_call[1]["message"]
        
        # Verify completion notification was sent
        last_call = mock_whatsapp_service.send_text_message.call_args_list[-1]
        assert "successfully" in last_call[1]["message"].lower()
        assert "5" in last_call[1]["message"]  # chunks created
        
        # Step 2: User asks question about the document
        query_result = await crew_manager.process_simple_message(
            user_id=user_id,
            phone_number=phone_number,
            message="What's in the document I just uploaded?"
        )
        
        # Verify response includes document content
        assert query_result["success"] is True
        assert "uploaded document" in query_result["response"].lower()
    
    @pytest.mark.asyncio
    async def test_image_upload_with_ocr(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test uploading image with OCR processing."""
        # Mock OCR result
        mock_rag_ingestion_service.ingest_document = AsyncMock(return_value={
            "success": True,
            "document_id": "img-456",
            "chunks_created": 2,
            "filename": "screenshot.png",
            "ocr_used": True
        })
        
        media_info = {
            "type": "imageMessage",
            "data": {
                "url": "https://example.com/screenshot.png",
                "mimetype": "image/png",
                "fileName": "screenshot.png"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        # Verify OCR was used
        assert result["success"] is True
        assert result["ocr_used"] is True
        
        # Verify appropriate notification
        notification_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "successfully" in notification_msg.lower()
    
    @pytest.mark.asyncio
    async def test_docx_upload_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test uploading DOCX document."""
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/report.docx",
                "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "fileName": "report.docx"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info,
            caption="Monthly report"
        )
        
        assert result["success"] is True
        assert "report.docx" in result["filename"]
    
    @pytest.mark.asyncio
    async def test_xlsx_upload_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test uploading Excel spreadsheet."""
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/data.xlsx",
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "fileName": "data.xlsx"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is True
        assert "data.xlsx" in result["filename"]
    
    @pytest.mark.asyncio
    async def test_pptx_upload_journey(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test uploading PowerPoint presentation."""
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/slides.pptx",
                "mimetype": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "fileName": "slides.pptx"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is True
        assert "slides.pptx" in result["filename"]


class TestFileUploadErrors:
    """Test error handling in file upload."""
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test handling of files exceeding size limit."""
        # Mock file too large error
        mock_rag_ingestion_service.ingest_document = AsyncMock(return_value={
            "success": False,
            "error": "File size exceeds 16MB limit",
            "error_type": "file_too_large"
        })
        
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/huge.pdf",
                "mimetype": "application/pdf",
                "fileName": "huge.pdf"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "16MB" in result["error"]
        
        # Verify error notification
        error_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "too large" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_upload_unsupported_file_type(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test handling of unsupported file types."""
        mock_rag_ingestion_service.ingest_document = AsyncMock(return_value={
            "success": False,
            "error": "Unsupported file type: video/mp4",
            "error_type": "unsupported_type"
        })
        
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/video.mp4",
                "mimetype": "video/mp4",
                "fileName": "video.mp4"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is False
        assert "Unsupported" in result["error"]
        
        # Verify helpful error message
        error_msg = mock_whatsapp_service.send_text_message.call_args[1]["message"]
        assert "supported" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_upload_corrupted_file(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test handling of corrupted files."""
        mock_rag_ingestion_service.ingest_document = AsyncMock(return_value={
            "success": False,
            "error": "Failed to extract text: corrupted file",
            "error_type": "processing_error"
        })
        
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/corrupted.pdf",
                "mimetype": "application/pdf",
                "fileName": "corrupted.pdf"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is False
        assert "corrupted" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_download_failure(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test handling of media download failures."""
        # Mock download failure
        mock_whatsapp_service.download_media = AsyncMock(
            side_effect=Exception("Failed to download media")
        )
        
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/document.pdf",
                "mimetype": "application/pdf",
                "fileName": "document.pdf"
            }
        }
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info
        )
        
        assert result["success"] is False


class TestMultipleFileUploads:
    """Test handling of multiple file uploads."""
    
    @pytest.mark.asyncio
    async def test_sequential_file_uploads(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test uploading multiple files in sequence."""
        files = [
            ("doc1.pdf", "application/pdf"),
            ("doc2.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("sheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        ]
        
        results = []
        for filename, mimetype in files:
            media_info = {
                "type": "documentMessage",
                "data": {
                    "url": f"https://example.com/{filename}",
                    "mimetype": mimetype,
                    "fileName": filename
                }
            }
            
            result = await crew_manager.process_file_upload(
                user_id="test-user",
                phone_number="+1234567890",
                media_info=media_info
            )
            results.append(result)
        
        # All should succeed
        assert all(r["success"] for r in results)
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_query_across_multiple_files(
        self,
        crew_manager,
        mock_retrieval_agent,
        mock_whatsapp_service
    ):
        """Test querying information from multiple uploaded files."""
        # Mock search results from multiple files
        mock_retrieval_agent.search_knowledge_base = AsyncMock(return_value=[
            {
                "text": "Info from file 1",
                "metadata": {"filename": "doc1.pdf"}
            },
            {
                "text": "Info from file 2",
                "metadata": {"filename": "doc2.docx"}
            }
        ])
        
        result = await crew_manager.process_simple_message(
            user_id="test-user",
            phone_number="+1234567890",
            message="What information is in my uploaded files?"
        )
        
        assert result["success"] is True
        # Response should synthesize information from multiple files
        assert result["has_context"] is True


class TestFileUploadWithCaption:
    """Test file uploads with captions."""
    
    @pytest.mark.asyncio
    async def test_upload_with_descriptive_caption(
        self,
        crew_manager,
        mock_whatsapp_service,
        mock_rag_ingestion_service
    ):
        """Test that captions are processed with the file."""
        media_info = {
            "type": "documentMessage",
            "data": {
                "url": "https://example.com/report.pdf",
                "mimetype": "application/pdf",
                "fileName": "report.pdf"
            }
        }
        
        caption = "This is the Q4 financial report with revenue projections"
        
        result = await crew_manager.process_file_upload(
            user_id="test-user",
            phone_number="+1234567890",
            media_info=media_info,
            caption=caption
        )
        
        assert result["success"] is True
        # Caption should be included in processing
        mock_rag_ingestion_service.ingest_document.assert_called_once()


class TestFileUploadIntegration:
    """Integration tests for file upload components."""
    
    @pytest.mark.asyncio
    async def test_tool_agent_file_processing(
        self,
        tool_agent,
        mock_rag_ingestion_service
    ):
        """Test tool agent file processing."""
        result = await tool_agent.process_file_upload(
            user_id="test-user",
            filename="test.pdf",
            file_content=b"fake_pdf_content",
            mime_type="application/pdf"
        )
        
        assert result["success"] is True
        assert "document_id" in result
        assert result["chunks_created"] == 5
    
    @pytest.mark.asyncio
    async def test_tool_agent_without_rag_service(
        self,
        mock_knowledge_base_service,
        mock_whatsapp_service
    ):
        """Test tool agent when RAG service not available."""
        agent = ToolAgent(
            knowledge_base_service=mock_knowledge_base_service,
            whatsapp_service=mock_whatsapp_service,
            rag_ingestion_service=None  # No RAG service
        )
        
        result = await agent.process_file_upload(
            user_id="test-user",
            filename="test.pdf",
            file_content=b"content",
            mime_type="application/pdf"
        )
        
        assert result["success"] is False
        assert "not available" in result["error"].lower()
