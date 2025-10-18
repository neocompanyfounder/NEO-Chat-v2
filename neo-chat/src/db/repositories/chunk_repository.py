"""Chunk repository with vector search capabilities."""

from typing import Optional
from uuid import UUID

from ...models.chunk import Chunk, ChunkCreate, ChunkWithEmbedding
from ...utils.logger import logger
from ..supabase_client import SupabaseClient


class ChunkRepository:
    """Repository for chunk database operations with vector search."""
    
    def __init__(self, db_client: SupabaseClient):
        """Initialize repository.
        
        Args:
            db_client: Supabase database client
        """
        self.db = db_client
    
    async def create(self, chunk: ChunkCreate) -> Chunk:
        """Create a new chunk.
        
        Args:
            chunk: Chunk creation data
            
        Returns:
            Created chunk
        """
        query = """
            INSERT INTO chunks (document_id, user_id, content, chunk_index, token_count)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, document_id, user_id, content, chunk_index, token_count, created_at
        """
        
        row = await self.db.fetchrow(
            query,
            chunk.document_id,
            chunk.user_id,
            chunk.content,
            chunk.chunk_index,
            chunk.token_count,
            user_id=str(chunk.user_id)
        )
        
        logger.info(
            f"Created chunk for document {chunk.document_id}",
            extra={
                "event_type": "chunk_created",
                "user_id": str(chunk.user_id),
                "metadata": {
                    "document_id": str(chunk.document_id),
                    "chunk_index": chunk.chunk_index
                }
            }
        )
        
        return Chunk(**dict(row))
    
    async def get_by_id(self, chunk_id: UUID, user_id: UUID) -> Optional[Chunk]:
        """Get chunk by ID.
        
        Args:
            chunk_id: Chunk's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            Chunk if found, None otherwise
        """
        query = """
            SELECT id, document_id, user_id, content, chunk_index, token_count, created_at
            FROM chunks
            WHERE id = $1 AND user_id = $2
        """
        
        row = await self.db.fetchrow(query, chunk_id, user_id, user_id=str(user_id))
        
        if row:
            return Chunk(**dict(row))
        return None
    
    async def get_by_document(self, document_id: UUID, user_id: UUID) -> list[Chunk]:
        """Get all chunks for a document.
        
        Args:
            document_id: Document's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            List of chunks ordered by chunk_index
        """
        query = """
            SELECT id, document_id, user_id, content, chunk_index, token_count, created_at
            FROM chunks
            WHERE document_id = $1 AND user_id = $2
            ORDER BY chunk_index ASC
        """
        
        rows = await self.db.fetch(query, document_id, user_id, user_id=str(user_id))
        
        return [Chunk(**dict(row)) for row in rows]
    
    async def search_similar(
        self,
        user_id: UUID,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.7
    ) -> list[ChunkWithEmbedding]:
        """Search for similar chunks using vector similarity.
        
        Uses HNSW index with cosine similarity as specified in FR-017a, FR-017b.
        Returns top-K chunks with similarity >= threshold.
        
        Args:
            user_id: User ID to search within
            query_embedding: Query embedding vector (768 dimensions)
            top_k: Number of results to return (default: 5)
            threshold: Minimum similarity threshold (default: 0.7)
            
        Returns:
            List of chunks with embeddings and similarity scores
        """
        query = """
            SELECT 
                c.id, c.document_id, c.user_id, c.content, 
                c.chunk_index, c.token_count, c.created_at,
                e.embedding,
                1 - (e.embedding <=> $1::vector) as similarity_score
            FROM chunks c
            JOIN embeddings e ON c.id = e.chunk_id
            WHERE c.user_id = $2
              AND 1 - (e.embedding <=> $1::vector) >= $3
            ORDER BY e.embedding <=> $1::vector
            LIMIT $4
        """
        
        rows = await self.db.fetch(
            query,
            query_embedding,
            user_id,
            threshold,
            top_k,
            user_id=str(user_id)
        )
        
        results = [ChunkWithEmbedding(**dict(row)) for row in rows]
        
        logger.info(
            f"Vector search returned {len(results)} chunks",
            extra={
                "event_type": "vector_search",
                "user_id": str(user_id),
                "metadata": {
                    "results_count": len(results),
                    "top_k": top_k,
                    "threshold": threshold
                }
            }
        )
        
        return results
    
    async def delete_by_document(self, document_id: UUID, user_id: UUID) -> int:
        """Delete all chunks for a document.
        
        Args:
            document_id: Document's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            Number of chunks deleted
        """
        query = "DELETE FROM chunks WHERE document_id = $1 AND user_id = $2"
        
        result = await self.db.execute(query, document_id, user_id, user_id=str(user_id))
        
        # Parse result like "DELETE 5"
        count = int(result.split()[-1]) if result.startswith("DELETE") else 0
        
        logger.info(
            f"Deleted {count} chunks for document {document_id}",
            extra={
                "event_type": "chunks_deleted",
                "user_id": str(user_id),
                "metadata": {
                    "document_id": str(document_id),
                    "count": count
                }
            }
        )
        
        return count
    
    async def delete(self, chunk_id: UUID, user_id: UUID) -> bool:
        """Delete a specific chunk.
        
        Args:
            chunk_id: Chunk's unique identifier
            user_id: User ID for RLS context
            
        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM chunks WHERE id = $1 AND user_id = $2"
        
        result = await self.db.execute(query, chunk_id, user_id, user_id=str(user_id))
        
        return result == "DELETE 1"
