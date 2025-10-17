"""RAG ingestion pipeline service.

This module orchestrates the complete RAG ingestion pipeline:
extract → chunk → embed → store
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.models.document import Document, DocumentCreate, DocumentUpdate, DocumentType, ProcessingStatus
from src.db.repositories.document_repository import DocumentRepository
from src.db.repositories.chunk_repository import ChunkRepository
from src.services.file_processor import FileProcessor, FileProcessorError
from src.services.vision_service import VisionService, VisionServiceError
from src.services.chunking_service import ChunkingService
from src.services.gemini_service import GeminiService
from src.services.vector_service import VectorService
from src.utils.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGIngestionService:
    """Service for RAG ingestion pipeline."""
    
    def __init__(self, settings: Settings):
        """Initialize RAG ingestion service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        
        # Initialize services
        self.document_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository()
        self.file_processor = FileProcessor()
        self.vision_service = VisionService(settings)
        self.chunking_service = ChunkingService(settings)
        self.gemini_service = GeminiService(settings)
        self.vector_service = VectorService(settings)
        
        logger.info("RAG ingestion service initialized")
    
    async def validate_file_size(self, file_size: int, filename: str) -> tuple[bool, Optional[str]]:
        """Validate file size is within limits (T054).
        
        Args:
            file_size: File size in bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size > self.max_file_size:
            error_msg = (
                f"File '{filename}' exceeds the maximum size limit of "
                f"{self.settings.MAX_FILE_SIZE_MB}MB. "
                f"Your file is {file_size / (1024 * 1024):.2f}MB."
            )
            logger.warning(
                "File size validation failed",
                extra={
                    "filename": filename,
                    "file_size": file_size,
                    "max_size": self.max_file_size
                }
            )
            return False, error_msg
        
        return True, None
    
    def detect_file_type(self, filename: str, mime_type: str) -> DocumentType:
        """Detect and validate file type (T055).
        
        Args:
            filename: Original filename
            mime_type: MIME type
            
        Returns:
            Detected document type
        """
        file_type = self.file_processor.detect_file_type(filename, mime_type)
        
        logger.info(
            "File type detected",
            extra={
                "filename": filename,
                "mime_type": mime_type,
                "detected_type": file_type.value
            }
        )
        
        return file_type
    
    async def ingest_document(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        mime_type: str,
        storage_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete RAG ingestion pipeline (T056).
        
        This method orchestrates the full pipeline:
        1. Validate file size
        2. Detect file type
        3. Create document record
        4. Extract text
        5. Chunk text
        6. Generate embeddings
        7. Store in vector database
        8. Update document status
        
        Args:
            user_id: User identifier
            filename: Original filename
            file_content: Raw file bytes
            mime_type: MIME type
            storage_path: Optional storage path
            
        Returns:
            Dictionary with ingestion results
            
        Raises:
            Exception: If ingestion fails
        """
        file_size = len(file_content)
        
        # Step 1: Validate file size
        is_valid, error_msg = await self.validate_file_size(file_size, filename)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "error_type": "file_size_exceeded"
            }
        
        # Step 2: Detect file type
        file_type = self.detect_file_type(filename, mime_type)
        
        if file_type == DocumentType.UNKNOWN:
            error_msg = f"Unsupported file type: {filename}"
            logger.warning(error_msg, extra={"filename": filename, "mime_type": mime_type})
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unsupported_file_type"
            }
        
        # Step 3: Create document record
        try:
            document_create = DocumentCreate(
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=storage_path,
                metadata={}
            )
            
            document = await self.document_repo.create(document_create)
            document_id = document.id
            
            logger.info(
                "Document record created",
                extra={
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": filename
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create document record: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create document record: {str(e)}",
                "error_type": "database_error"
            }
        
        # Update document status to processing
        try:
            await self.document_repo.update(
                document_id,
                DocumentUpdate(status=ProcessingStatus.PROCESSING)
            )
        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")
        
        # Step 4: Extract text
        try:
            if file_type == DocumentType.IMAGE:
                # Use Vision API for OCR
                extraction_result = await self.vision_service.extract_text_from_image(
                    file_content,
                    filename
                )
            else:
                # Use file processor for documents
                extraction_result = await self.file_processor.extract_text(
                    file_content,
                    file_type,
                    filename
                )
            
            extracted_text = extraction_result["text"]
            extraction_metadata = extraction_result["metadata"]
            
            if not extracted_text or not extracted_text.strip():
                error_msg = "No text could be extracted from the file"
                await self.document_repo.update(
                    document_id,
                    DocumentUpdate(
                        status=ProcessingStatus.FAILED,
                        processing_error=error_msg
                    )
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "no_text_extracted",
                    "document_id": document_id
                }
            
            logger.info(
                "Text extracted successfully",
                extra={
                    "document_id": document_id,
                    "text_length": len(extracted_text),
                    "metadata": extraction_metadata
                }
            )
            
        except (FileProcessorError, VisionServiceError) as e:
            error_msg = f"Text extraction failed: {str(e)}"
            logger.error(error_msg, extra={"document_id": document_id})
            
            await self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status=ProcessingStatus.FAILED,
                    processing_error=error_msg
                )
            )
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "extraction_error",
                "document_id": document_id
            }
        
        # Step 5: Chunk text
        try:
            chunk_metadata = {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type.value,
                "user_id": user_id,
                **extraction_metadata
            }
            
            chunks = await self.chunking_service.chunk_text(
                extracted_text,
                chunk_metadata
            )
            
            if not chunks:
                error_msg = "No chunks created from extracted text"
                await self.document_repo.update(
                    document_id,
                    DocumentUpdate(
                        status=ProcessingStatus.FAILED,
                        processing_error=error_msg
                    )
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "chunking_error",
                    "document_id": document_id
                }
            
            logger.info(
                f"Created {len(chunks)} chunks",
                extra={
                    "document_id": document_id,
                    "chunks_count": len(chunks)
                }
            )
            
        except Exception as e:
            error_msg = f"Chunking failed: {str(e)}"
            logger.error(error_msg, extra={"document_id": document_id})
            
            await self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status=ProcessingStatus.FAILED,
                    processing_error=error_msg
                )
            )
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "chunking_error",
                "document_id": document_id
            }
        
        # Step 6 & 7: Generate embeddings and store in vector database
        try:
            stored_chunks = 0
            
            for chunk in chunks:
                # Generate embedding
                embedding = await self.gemini_service.generate_embedding(
                    chunk["text"],
                    task_type="retrieval_document"
                )
                
                # Store chunk and embedding
                chunk_id = await self.chunk_repo.create(
                    user_id=user_id,
                    content=chunk["text"],
                    metadata=chunk["metadata"]
                )
                
                # Store embedding in vector database
                await self.vector_service.store_embedding(
                    user_id=user_id,
                    chunk_id=chunk_id,
                    embedding=embedding,
                    metadata=chunk["metadata"]
                )
                
                stored_chunks += 1
            
            logger.info(
                f"Stored {stored_chunks} chunks with embeddings",
                extra={
                    "document_id": document_id,
                    "chunks_stored": stored_chunks
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to store embeddings: {str(e)}"
            logger.error(error_msg, extra={"document_id": document_id})
            
            await self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status=ProcessingStatus.FAILED,
                    processing_error=error_msg
                )
            )
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "storage_error",
                "document_id": document_id,
                "chunks_processed": stored_chunks
            }
        
        # Step 8: Update document status to completed
        try:
            await self.document_repo.update(
                document_id,
                DocumentUpdate(
                    status=ProcessingStatus.COMPLETED,
                    chunks_count=stored_chunks,
                    processed_at=datetime.utcnow(),
                    metadata={**extraction_metadata, "chunks_count": stored_chunks}
                )
            )
            
            logger.info(
                "Document ingestion completed successfully",
                extra={
                    "document_id": document_id,
                    "chunks_count": stored_chunks,
                    "filename": filename
                }
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_count": stored_chunks,
                "filename": filename,
                "file_type": file_type.value,
                "metadata": extraction_metadata
            }
            
        except Exception as e:
            logger.error(
                f"Failed to update final document status: {str(e)}",
                extra={"document_id": document_id}
            )
            
            # Document was processed successfully, just status update failed
            return {
                "success": True,
                "document_id": document_id,
                "chunks_count": stored_chunks,
                "filename": filename,
                "file_type": file_type.value,
                "warning": "Document processed but status update failed"
            }
