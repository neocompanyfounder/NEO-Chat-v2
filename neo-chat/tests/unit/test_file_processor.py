"""Unit tests for file processor service (T059)."""

import pytest
from unittest.mock import Mock, patch, mock_open
from io import BytesIO
from src.services.file_processor import FileProcessor, FileProcessorError
from src.models.document import DocumentType


@pytest.fixture
def file_processor():
    """Create file processor instance."""
    return FileProcessor()


class TestFileTypeDetection:
    """Test file type detection functionality."""
    
    def test_detect_pdf_by_extension(self, file_processor):
        """Test PDF detection by file extension."""
        file_type = file_processor.detect_file_type("document.pdf", "application/pdf")
        assert file_type == DocumentType.PDF
    
    def test_detect_pdf_by_mime_type(self, file_processor):
        """Test PDF detection by MIME type."""
        file_type = file_processor.detect_file_type("document", "application/pdf")
        assert file_type == DocumentType.PDF
    
    def test_detect_docx(self, file_processor):
        """Test DOCX detection."""
        file_type = file_processor.detect_file_type(
            "document.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert file_type == DocumentType.DOCX
    
    def test_detect_xlsx(self, file_processor):
        """Test XLSX detection."""
        file_type = file_processor.detect_file_type(
            "spreadsheet.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert file_type == DocumentType.XLSX
    
    def test_detect_pptx(self, file_processor):
        """Test PPTX detection."""
        file_type = file_processor.detect_file_type(
            "presentation.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        assert file_type == DocumentType.PPTX
    
    def test_detect_txt(self, file_processor):
        """Test TXT detection."""
        file_type = file_processor.detect_file_type("notes.txt", "text/plain")
        assert file_type == DocumentType.TXT
    
    def test_detect_image_jpg(self, file_processor):
        """Test JPG image detection."""
        file_type = file_processor.detect_file_type("photo.jpg", "image/jpeg")
        assert file_type == DocumentType.IMAGE
    
    def test_detect_image_png(self, file_processor):
        """Test PNG image detection."""
        file_type = file_processor.detect_file_type("screenshot.png", "image/png")
        assert file_type == DocumentType.IMAGE
    
    def test_detect_unsupported_type(self, file_processor):
        """Test detection of unsupported file type."""
        with pytest.raises(FileProcessorError) as exc_info:
            file_processor.detect_file_type("video.mp4", "video/mp4")
        assert "Unsupported file type" in str(exc_info.value)


class TestPDFExtraction:
    """Test PDF text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_from_pdf_success(self, file_processor):
        """Test successful PDF text extraction."""
        # Mock PDF content
        mock_pdf_content = b"%PDF-1.4 mock content"
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            # Mock PDF reader
            mock_page = Mock()
            mock_page.extract_text.return_value = "This is page 1 content.\n"
            
            mock_pdf = Mock()
            mock_pdf.pages = [mock_page, mock_page]  # 2 pages
            mock_pdf.metadata = {
                '/Title': 'Test Document',
                '/Author': 'Test Author'
            }
            
            mock_reader.return_value = mock_pdf
            
            result = await file_processor._extract_from_pdf(
                mock_pdf_content,
                "test.pdf"
            )
            
            assert result["success"] is True
            assert "This is page 1 content" in result["text"]
            assert result["metadata"]["pages"] == 2
            assert result["metadata"]["title"] == "Test Document"
    
    @pytest.mark.asyncio
    async def test_extract_from_pdf_empty(self, file_processor):
        """Test PDF with no extractable text."""
        mock_pdf_content = b"%PDF-1.4 mock content"
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            
            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_pdf.metadata = {}
            
            mock_reader.return_value = mock_pdf
            
            with pytest.raises(FileProcessorError) as exc_info:
                await file_processor._extract_from_pdf(mock_pdf_content, "test.pdf")
            
            assert "No text content" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_from_pdf_corrupted(self, file_processor):
        """Test corrupted PDF handling."""
        mock_pdf_content = b"corrupted data"
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_reader.side_effect = Exception("Invalid PDF")
            
            with pytest.raises(FileProcessorError) as exc_info:
                await file_processor._extract_from_pdf(mock_pdf_content, "test.pdf")
            
            assert "Failed to extract" in str(exc_info.value)


class TestDOCXExtraction:
    """Test DOCX text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_from_docx_success(self, file_processor):
        """Test successful DOCX text extraction."""
        mock_docx_content = b"mock docx content"
        
        with patch('docx.Document') as mock_doc_class:
            # Mock paragraphs
            mock_para1 = Mock()
            mock_para1.text = "First paragraph."
            mock_para2 = Mock()
            mock_para2.text = "Second paragraph."
            
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_para1, mock_para2]
            mock_doc.core_properties.title = "Test Document"
            mock_doc.core_properties.author = "Test Author"
            
            mock_doc_class.return_value = mock_doc
            
            result = await file_processor._extract_from_docx(
                mock_docx_content,
                "test.docx"
            )
            
            assert result["success"] is True
            assert "First paragraph" in result["text"]
            assert "Second paragraph" in result["text"]
            assert result["metadata"]["title"] == "Test Document"
    
    @pytest.mark.asyncio
    async def test_extract_from_docx_empty(self, file_processor):
        """Test DOCX with no content."""
        mock_docx_content = b"mock docx content"
        
        with patch('docx.Document') as mock_doc_class:
            mock_doc = Mock()
            mock_doc.paragraphs = []
            mock_doc.core_properties.title = None
            
            mock_doc_class.return_value = mock_doc
            
            with pytest.raises(FileProcessorError) as exc_info:
                await file_processor._extract_from_docx(mock_docx_content, "test.docx")
            
            assert "No text content" in str(exc_info.value)


class TestXLSXExtraction:
    """Test XLSX text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_from_xlsx_success(self, file_processor):
        """Test successful XLSX text extraction."""
        mock_xlsx_content = b"mock xlsx content"
        
        with patch('openpyxl.load_workbook') as mock_wb:
            # Mock cells
            mock_cell1 = Mock()
            mock_cell1.value = "Header 1"
            mock_cell2 = Mock()
            mock_cell2.value = "Header 2"
            mock_cell3 = Mock()
            mock_cell3.value = "Data 1"
            mock_cell4 = Mock()
            mock_cell4.value = "Data 2"
            
            # Mock worksheet
            mock_sheet = Mock()
            mock_sheet.title = "Sheet1"
            mock_sheet.iter_rows.return_value = [
                [mock_cell1, mock_cell2],
                [mock_cell3, mock_cell4]
            ]
            
            # Mock workbook
            mock_workbook = Mock()
            mock_workbook.sheetnames = ["Sheet1"]
            mock_workbook.__getitem__ = Mock(return_value=mock_sheet)
            
            mock_wb.return_value = mock_workbook
            
            result = await file_processor._extract_from_xlsx(
                mock_xlsx_content,
                "test.xlsx"
            )
            
            assert result["success"] is True
            assert "Header 1" in result["text"]
            assert "Data 1" in result["text"]
            assert result["metadata"]["sheets"] == 1
    
    @pytest.mark.asyncio
    async def test_extract_from_xlsx_empty(self, file_processor):
        """Test XLSX with no content."""
        mock_xlsx_content = b"mock xlsx content"
        
        with patch('openpyxl.load_workbook') as mock_wb:
            mock_sheet = Mock()
            mock_sheet.title = "Sheet1"
            mock_sheet.iter_rows.return_value = []
            
            mock_workbook = Mock()
            mock_workbook.sheetnames = ["Sheet1"]
            mock_workbook.__getitem__ = Mock(return_value=mock_sheet)
            
            mock_wb.return_value = mock_workbook
            
            with pytest.raises(FileProcessorError) as exc_info:
                await file_processor._extract_from_xlsx(mock_xlsx_content, "test.xlsx")
            
            assert "No text content" in str(exc_info.value)


class TestPPTXExtraction:
    """Test PPTX text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_from_pptx_success(self, file_processor):
        """Test successful PPTX text extraction."""
        mock_pptx_content = b"mock pptx content"
        
        with patch('pptx.Presentation') as mock_prs_class:
            # Mock text frame
            mock_text_frame = Mock()
            mock_text_frame.text = "Slide content"
            
            # Mock shape
            mock_shape = Mock()
            mock_shape.has_text_frame = True
            mock_shape.text_frame = mock_text_frame
            
            # Mock slide
            mock_slide = Mock()
            mock_slide.shapes = [mock_shape]
            
            # Mock presentation
            mock_prs = Mock()
            mock_prs.slides = [mock_slide, mock_slide]
            
            mock_prs_class.return_value = mock_prs
            
            result = await file_processor._extract_from_pptx(
                mock_pptx_content,
                "test.pptx"
            )
            
            assert result["success"] is True
            assert "Slide content" in result["text"]
            assert result["metadata"]["slides"] == 2
    
    @pytest.mark.asyncio
    async def test_extract_from_pptx_empty(self, file_processor):
        """Test PPTX with no content."""
        mock_pptx_content = b"mock pptx content"
        
        with patch('pptx.Presentation') as mock_prs_class:
            mock_slide = Mock()
            mock_slide.shapes = []
            
            mock_prs = Mock()
            mock_prs.slides = [mock_slide]
            
            mock_prs_class.return_value = mock_prs
            
            with pytest.raises(FileProcessorError) as exc_info:
                await file_processor._extract_from_pptx(mock_pptx_content, "test.pptx")
            
            assert "No text content" in str(exc_info.value)


class TestTXTExtraction:
    """Test TXT text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_from_txt_utf8(self, file_processor):
        """Test UTF-8 text file extraction."""
        mock_txt_content = "This is plain text content.\nWith multiple lines.".encode('utf-8')
        
        result = await file_processor._extract_from_txt(
            mock_txt_content,
            "test.txt"
        )
        
        assert result["success"] is True
        assert "plain text content" in result["text"]
        assert "multiple lines" in result["text"]
    
    @pytest.mark.asyncio
    async def test_extract_from_txt_latin1(self, file_processor):
        """Test Latin-1 encoded text file."""
        mock_txt_content = "Text with special chars: café".encode('latin-1')
        
        result = await file_processor._extract_from_txt(
            mock_txt_content,
            "test.txt"
        )
        
        assert result["success"] is True
        assert "café" in result["text"] or "caf" in result["text"]  # Encoding fallback
    
    @pytest.mark.asyncio
    async def test_extract_from_txt_empty(self, file_processor):
        """Test empty text file."""
        mock_txt_content = b""
        
        with pytest.raises(FileProcessorError) as exc_info:
            await file_processor._extract_from_txt(mock_txt_content, "test.txt")
        
        assert "No text content" in str(exc_info.value)


class TestExtractText:
    """Test main extract_text method."""
    
    @pytest.mark.asyncio
    async def test_extract_text_routes_to_pdf(self, file_processor):
        """Test that PDF files are routed to PDF extractor."""
        mock_content = b"%PDF-1.4 content"
        
        with patch.object(file_processor, '_extract_from_pdf') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "PDF content",
                "metadata": {}
            }
            
            result = await file_processor.extract_text(
                mock_content,
                DocumentType.PDF,
                "test.pdf"
            )
            
            assert result["success"] is True
            mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_routes_to_docx(self, file_processor):
        """Test that DOCX files are routed to DOCX extractor."""
        mock_content = b"docx content"
        
        with patch.object(file_processor, '_extract_from_docx') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "DOCX content",
                "metadata": {}
            }
            
            result = await file_processor.extract_text(
                mock_content,
                DocumentType.DOCX,
                "test.docx"
            )
            
            assert result["success"] is True
            mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_unsupported_type(self, file_processor):
        """Test extraction with unsupported file type."""
        mock_content = b"content"
        
        with pytest.raises(FileProcessorError) as exc_info:
            await file_processor.extract_text(
                mock_content,
                DocumentType.IMAGE,  # Images should use vision service
                "test.jpg"
            )
        
        assert "not supported" in str(exc_info.value).lower()


class TestDependencyValidation:
    """Test dependency validation."""
    
    def test_validate_dependencies_success(self, file_processor):
        """Test that all dependencies are available."""
        # Should not raise any exception
        file_processor._validate_dependencies()
    
    def test_validate_dependencies_missing(self):
        """Test handling of missing dependencies."""
        with patch('src.services.file_processor.PYPDF2_AVAILABLE', False):
            with pytest.raises(FileProcessorError) as exc_info:
                FileProcessor()
            
            assert "PyPDF2" in str(exc_info.value)
