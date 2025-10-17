"""Document repository for database operations.

This module provides CRUD operations for documents in the database.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from src.models.document import Document, DocumentCreate, DocumentUpdate, ProcessingStatus
from src.db.supabase_client import get_supabase_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document database operations."""
    
    def __init__(self):
        """Initialize document repository."""
        self.client = get_supabase_client()
    
    async def create(self, document: DocumentCreate) -> Document:
        """Create a new document record.
        
        Args:
            document: Document creation data
            
        Returns:
            Created document with ID
            
        Raises:
            Exception: If database operation fails
        """
        try:
            doc_id = str(uuid.uuid4())
            
            async with self.client.acquire() as conn:
                query = """
                    INSERT INTO documents (
                        id, user_id, filename, file_type, file_size, mime_type,
                        storage_path, status, chunks_count, uploaded_at, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    doc_id,
                    document.user_id,
                    document.filename,
                    document.file_type.value,
                    document.file_size,
                    document.mime_type,
                    document.storage_path,
                    ProcessingStatus.PENDING.value,
                    0,
                    datetime.utcnow(),
                    document.metadata
                )
                
                logger.info(
                    "Document created",
                    extra={
                        "document_id": doc_id,
                        "user_id": document.user_id,
                        "filename": document.filename,
                        "file_size": document.file_size
                    }
                )
                
                return Document(**dict(row))
                
        except Exception as e:
            logger.error(
                f"Failed to create document: {str(e)}",
                extra={
                    "user_id": document.user_id,
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            raise
    
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document if found, None otherwise
        """
        try:
            async with self.client.acquire() as conn:
                query = "SELECT * FROM documents WHERE id = $1"
                row = await conn.fetchrow(query, document_id)
                
                if row:
                    return Document(**dict(row))
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to get document: {str(e)}",
                extra={"document_id": document_id, "error": str(e)}
            )
            raise
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Get all documents for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of documents
        """
        try:
            async with self.client.acquire() as conn:
                query = """
                    SELECT * FROM documents
                    WHERE user_id = $1
                    ORDER BY uploaded_at DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, user_id, limit, offset)
                
                return [Document(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(
                f"Failed to get user documents: {str(e)}",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
    
    async def update(self, document_id: str, update: DocumentUpdate) -> Optional[Document]:
        """Update document status and metadata.
        
        Args:
            document_id: Document identifier
            update: Update data
            
        Returns:
            Updated document if found, None otherwise
        """
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            param_count = 1
            
            if update.status is not None:
                update_fields.append(f"status = ${param_count}")
                values.append(update.status.value)
                param_count += 1
            
            if update.chunks_count is not None:
                update_fields.append(f"chunks_count = ${param_count}")
                values.append(update.chunks_count)
                param_count += 1
            
            if update.processing_error is not None:
                update_fields.append(f"processing_error = ${param_count}")
                values.append(update.processing_error)
                param_count += 1
            
            if update.processed_at is not None:
                update_fields.append(f"processed_at = ${param_count}")
                values.append(update.processed_at)
                param_count += 1
            
            if update.metadata is not None:
                update_fields.append(f"metadata = ${param_count}")
                values.append(update.metadata)
                param_count += 1
            
            if not update_fields:
                # No updates to perform
                return await self.get_by_id(document_id)
            
            values.append(document_id)
            
            async with self.client.acquire() as conn:
                query = f"""
                    UPDATE documents
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                    RETURNING *
                """
                
                row = await conn.fetchrow(query, *values)
                
                if row:
                    logger.info(
                        "Document updated",
                        extra={
                            "document_id": document_id,
                            "updates": update_fields
                        }
                    )
                    return Document(**dict(row))
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to update document: {str(e)}",
                extra={"document_id": document_id, "error": str(e)}
            )
            raise
    
    async def delete(self, document_id: str) -> bool:
        """Delete a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.client.acquire() as conn:
                query = "DELETE FROM documents WHERE id = $1"
                result = await conn.execute(query, document_id)
                
                deleted = result.split()[-1] == "1"
                
                if deleted:
                    logger.info(
                        "Document deleted",
                        extra={"document_id": document_id}
                    )
                
                return deleted
                
        except Exception as e:
            logger.error(
                f"Failed to delete document: {str(e)}",
                extra={"document_id": document_id, "error": str(e)}
            )
            raise
    
    async def delete_by_user(self, user_id: str) -> int:
        """Delete all documents for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of documents deleted
        """
        try:
            async with self.client.acquire() as conn:
                query = "DELETE FROM documents WHERE user_id = $1"
                result = await conn.execute(query, user_id)
                
                count = int(result.split()[-1])
                
                logger.info(
                    "User documents deleted",
                    extra={"user_id": user_id, "count": count}
                )
                
                return count
                
        except Exception as e:
            logger.error(
                f"Failed to delete user documents: {str(e)}",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
    
    async def get_pending_documents(self, limit: int = 10) -> List[Document]:
        """Get documents pending processing.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of pending documents
        """
        try:
            async with self.client.acquire() as conn:
                query = """
                    SELECT * FROM documents
                    WHERE status = $1
                    ORDER BY uploaded_at ASC
                    LIMIT $2
                """
                rows = await conn.fetch(query, ProcessingStatus.PENDING.value, limit)
                
                return [Document(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(
                f"Failed to get pending documents: {str(e)}",
                extra={"error": str(e)}
            )
            raise
