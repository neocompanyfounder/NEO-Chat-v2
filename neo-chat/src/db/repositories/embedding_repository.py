"""Embedding repository for vector operations."""

from typing import Optional
from uuid import UUID

from ...utils.logger import logger
from ..supabase_client import SupabaseClient


class EmbeddingRepository:
    """Repository for embedding vector operations."""
    
    def __init__(self, db_client: SupabaseClient):
        """Initialize repository.
        
        Args:
            db_client: Supabase database client
        """
        self.db = db_client
    
    async def create(
        self,
        chunk_id: UUID,
        user_id: UUID,
        embedding: list[float]
    ) -> UUID:
        """Create embedding for a chunk.
        
        Args:
            chunk_id: Chunk's unique identifier
            user_id: User ID for RLS context
            embedding: 768-dimensional embedding vector
            
        Returns:
            Created embedding ID
        """
        query = """
            INSERT INTO embeddings (chunk_id, user_id, embedding)
            VALUES ($1, $2, $3::vector)
            RETURNING id
        """
        
        row = await self.db.fetchrow(
            query,
            chunk_id,
            user_id,
            embedding,
            user_id=str(user_id)
        )
        
        logger.info(
            f"Created embedding for chunk {chunk_id}",
            extra={
                "event_type": "embedding_created",
                "user_id": str(user_id),
                "metadata": {
                    "chunk_id": str(chunk_id),
                    "dimension": len(embedding)
                }
            }
        )
        
        return row['id']
    
    async def get_by_chunk(self, chunk_id: UUID, user_id: UUID) -> Optional[list[float]]:
        """Get embedding for a chunk.
        
        Args:
            chunk_id: Chunk's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            Embedding vector if found, None otherwise
        """
        query = """
            SELECT embedding
            FROM embeddings
            WHERE chunk_id = $1 AND user_id = $2
        """
        
        row = await self.db.fetchrow(query, chunk_id, user_id, user_id=str(user_id))
        
        if row:
            return row['embedding']
        return None
    
    async def delete_by_chunk(self, chunk_id: UUID, user_id: UUID) -> bool:
        """Delete embedding for a chunk.
        
        Args:
            chunk_id: Chunk's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM embeddings WHERE chunk_id = $1 AND user_id = $2"
        
        result = await self.db.execute(query, chunk_id, user_id, user_id=str(user_id))
        
        return result == "DELETE 1"
    
    async def batch_create(
        self,
        embeddings: list[tuple[UUID, UUID, list[float]]],
        user_id: UUID
    ) -> int:
        """Batch create embeddings.
        
        Processes embeddings in batches of 100 as specified in FR-015c.
        
        Args:
            embeddings: List of (chunk_id, user_id, embedding) tuples
            user_id: User ID for RLS context
            
        Returns:
            Number of embeddings created
        """
        query = """
            INSERT INTO embeddings (chunk_id, user_id, embedding)
            VALUES ($1, $2, $3::vector)
        """
        
        count = 0
        batch_size = 100  # FR-015c: max 100 chunks per batch
        
        # Process in batches
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i+batch_size]
            
            async with self.db.acquire() as conn:
                # Set RLS context
                await conn.execute(f"SET app.current_user_id = '{user_id}'")
                
                for chunk_id, uid, emb in batch:
                    await conn.execute(query, chunk_id, uid, emb)
                    count += 1
            
            logger.info(
                f"Batch created {len(batch)} embeddings",
                extra={
                    "event_type": "batch_embeddings_created",
                    "user_id": str(user_id),
                    "metadata": {
                        "batch_size": len(batch),
                        "total_processed": count
                    }
                }
            )
        
        logger.info(
            f"Completed batch creation of {count} embeddings",
            extra={
                "event_type": "batch_creation_complete",
                "user_id": str(user_id),
                "metadata": {"total_count": count}
            }
        )
        
        return count
    
    async def delete_by_document(self, document_id: UUID, user_id: UUID) -> int:
        """Delete all embeddings for a document's chunks.
        
        Args:
            document_id: Document's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            Number of embeddings deleted
        """
        query = """
            DELETE FROM embeddings
            WHERE chunk_id IN (
                SELECT id FROM chunks WHERE document_id = $1 AND user_id = $2
            )
            AND user_id = $2
        """
        
        result = await self.db.execute(query, document_id, user_id, user_id=str(user_id))
        
        # Parse result like "DELETE 5"
        count = int(result.split()[-1]) if result.startswith("DELETE") else 0
        
        logger.info(
            f"Deleted {count} embeddings for document {document_id}",
            extra={
                "event_type": "embeddings_deleted",
                "user_id": str(user_id),
                "metadata": {
                    "document_id": str(document_id),
                    "count": count
                }
            }
        )
        
        return count
