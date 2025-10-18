"""Vector service for Supabase vector operations (T034)."""

from typing import List, Dict, Any, Optional
from src.db.supabase_client import get_supabase_client
from src.utils.config import Settings
from src.utils.logger import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


class VectorService:
    """Service for vector similarity search and storage in Supabase."""

    def __init__(self, settings: Settings):
        """Initialize vector service with Supabase configuration.
        
        Args:
            settings: Application settings containing Supabase credentials
        """
        self.settings = settings
        self.client = get_supabase_client(settings)
        self.similarity_threshold = settings.VECTOR_SIMILARITY_THRESHOLD
        self.top_k = settings.VECTOR_TOP_K

    @with_retry(max_retries=5, base_delay=1.0)
    async def store_embedding(
        self,
        chunk_id: str,
        user_id: str,
        embedding: List[float]
    ) -> Dict[str, Any]:
        """Store embedding vector in Supabase.
        
        Args:
            chunk_id: UUID of the chunk
            user_id: UUID of the user
            embedding: 768-dimensional embedding vector
            
        Returns:
            Stored embedding record
            
        Raises:
            Exception: If storage fails
        """
        logger.info(
            "Storing embedding",
            extra={
                "chunk_id": chunk_id,
                "user_id": user_id,
                "dimension": len(embedding)
            }
        )
        
        try:
            result = self.client.table("embeddings").insert({
                "chunk_id": chunk_id,
                "user_id": user_id,
                "embedding": embedding
            }).execute()
            
            logger.info(
                "Embedding stored successfully",
                extra={
                    "chunk_id": chunk_id,
                    "embedding_id": result.data[0]["id"] if result.data else None
                }
            )
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(
                "Embedding storage failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "chunk_id": chunk_id
                }
            )
            raise

    @with_retry(max_retries=5, base_delay=1.0)
    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector (768 dimensions)
            user_id: UUID of the user (for RLS filtering)
            top_k: Number of results to return (default from settings)
            threshold: Minimum similarity threshold (default from settings)
            
        Returns:
            List of similar chunks with content and similarity scores
            
        Raises:
            Exception: If search fails
        """
        k = top_k or self.top_k
        min_similarity = threshold or self.similarity_threshold
        
        logger.info(
            "Searching similar vectors",
            extra={
                "user_id": user_id,
                "top_k": k,
                "threshold": min_similarity
            }
        )
        
        try:
            # Use Supabase RPC function for vector similarity search
            # This assumes a PostgreSQL function exists for HNSW search
            result = self.client.rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": min_similarity,
                    "match_count": k,
                    "filter_user_id": user_id
                }
            ).execute()
            
            chunks = result.data if result.data else []
            
            logger.info(
                "Vector search completed",
                extra={
                    "user_id": user_id,
                    "results_count": len(chunks),
                    "top_k": k
                }
            )
            
            return chunks
            
        except Exception as e:
            logger.error(
                "Vector search failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            raise

    @with_retry(max_retries=5, base_delay=1.0)
    async def store_embeddings_batch(
        self,
        embeddings_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Store multiple embeddings in batch.
        
        Args:
            embeddings_data: List of dicts with chunk_id, user_id, embedding
            
        Returns:
            List of stored embedding records
            
        Raises:
            Exception: If batch storage fails
        """
        logger.info(
            "Storing batch embeddings",
            extra={
                "batch_size": len(embeddings_data)
            }
        )
        
        try:
            result = self.client.table("embeddings").insert(
                embeddings_data
            ).execute()
            
            stored_count = len(result.data) if result.data else 0
            
            logger.info(
                "Batch embeddings stored",
                extra={
                    "batch_size": len(embeddings_data),
                    "stored_count": stored_count
                }
            )
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(
                "Batch embedding storage failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "batch_size": len(embeddings_data)
                }
            )
            raise

    async def delete_user_embeddings(
        self,
        user_id: str
    ) -> int:
        """Delete all embeddings for a user (for knowledge base reset).
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Number of embeddings deleted
            
        Raises:
            Exception: If deletion fails
        """
        logger.info(
            "Deleting user embeddings",
            extra={
                "user_id": user_id
            }
        )
        
        try:
            result = self.client.table("embeddings").delete().eq(
                "user_id", user_id
            ).execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(
                "User embeddings deleted",
                extra={
                    "user_id": user_id,
                    "deleted_count": deleted_count
                }
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(
                "Embedding deletion failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            raise
