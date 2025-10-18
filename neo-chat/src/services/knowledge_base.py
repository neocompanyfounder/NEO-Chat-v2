"""Knowledge base service for conversation storage and retrieval (T035)."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.repositories.chunk_repository import ChunkRepository
from src.db.repositories.embedding_repository import EmbeddingRepository
from src.services.gemini_service import GeminiService
from src.services.vector_service import VectorService
from src.utils.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseService:
    """Service for managing user knowledge base (conversations, documents)."""

    def __init__(
        self,
        settings: Settings,
        gemini_service: GeminiService,
        vector_service: VectorService,
        chunk_repository: ChunkRepository,
        embedding_repository: EmbeddingRepository
    ):
        """Initialize knowledge base service.
        
        Args:
            settings: Application settings
            gemini_service: Gemini service for embeddings
            vector_service: Vector service for similarity search
            chunk_repository: Repository for chunk operations
            embedding_repository: Repository for embedding operations
        """
        self.settings = settings
        self.gemini_service = gemini_service
        self.vector_service = vector_service
        self.chunk_repository = chunk_repository
        self.embedding_repository = embedding_repository
        
        self.max_context_tokens = settings.MAX_CONTEXT_TOKENS
        self.min_chunk_tokens = settings.MIN_CHUNK_TOKENS
        self.max_chunk_tokens = settings.MAX_CHUNK_TOKENS

    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store conversation exchange in knowledge base.
        
        Args:
            user_id: UUID of the user
            user_message: User's message text
            ai_response: AI's response text
            metadata: Optional metadata (timestamp, message_id, etc.)
            
        Returns:
            Storage result with chunk and embedding IDs
            
        Raises:
            Exception: If storage fails
        """
        logger.info(
            "Storing conversation in knowledge base",
            extra={
                "user_id": user_id,
                "user_message_length": len(user_message),
                "ai_response_length": len(ai_response)
            }
        )
        
        try:
            # Create conversation text for storage
            timestamp = metadata.get("timestamp") if metadata else datetime.utcnow().isoformat()
            conversation_text = f"""[{timestamp}]
User: {user_message}
Assistant: {ai_response}"""
            
            # Create chunk for conversation
            chunk = await self.chunk_repository.create(
                user_id=user_id,
                document_id=None,  # Conversations don't have document_id
                content=conversation_text,
                chunk_index=0,
                token_count=len(conversation_text.split()),  # Rough estimate
                metadata={
                    "source": "conversation",
                    "timestamp": timestamp,
                    **(metadata or {})
                }
            )
            
            # Generate embedding for conversation
            embedding_vector = await self.gemini_service.generate_embedding(
                conversation_text,
                task_type="retrieval_document"
            )
            
            # Store embedding
            embedding = await self.vector_service.store_embedding(
                chunk_id=chunk["id"],
                user_id=user_id,
                embedding=embedding_vector
            )
            
            logger.info(
                "Conversation stored successfully",
                extra={
                    "user_id": user_id,
                    "chunk_id": chunk["id"],
                    "embedding_id": embedding.get("id")
                }
            )
            
            return {
                "chunk_id": chunk["id"],
                "embedding_id": embedding.get("id"),
                "stored_at": timestamp
            }
            
        except Exception as e:
            logger.error(
                "Conversation storage failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            raise

    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: Optional[int] = None
    ) -> str:
        """Retrieve relevant context from knowledge base for a query.
        
        Args:
            user_id: UUID of the user
            query: User's query text
            top_k: Number of chunks to retrieve (default from settings)
            
        Returns:
            Formatted context string for LLM
            
        Raises:
            Exception: If retrieval fails
        """
        logger.info(
            "Retrieving context from knowledge base",
            extra={
                "user_id": user_id,
                "query_length": len(query),
                "top_k": top_k
            }
        )
        
        try:
            # Generate query embedding
            query_embedding = await self.gemini_service.generate_embedding(
                query,
                task_type="retrieval_query"
            )
            
            # Search for similar chunks
            similar_chunks = await self.vector_service.search_similar(
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=top_k
            )
            
            if not similar_chunks:
                logger.info(
                    "No relevant context found",
                    extra={"user_id": user_id}
                )
                return ""
            
            # Format context for LLM
            context_parts = []
            total_tokens = 0
            
            for i, chunk in enumerate(similar_chunks, 1):
                content = chunk.get("content", "")
                similarity = chunk.get("similarity", 0.0)
                
                # Estimate tokens (rough approximation)
                chunk_tokens = len(content.split())
                
                # Stop if we exceed max context tokens
                if total_tokens + chunk_tokens > self.max_context_tokens:
                    logger.info(
                        "Context token limit reached",
                        extra={
                            "chunks_used": i - 1,
                            "total_tokens": total_tokens
                        }
                    )
                    break
                
                context_parts.append(
                    f"[Relevance: {similarity:.2f}]\n{content}"
                )
                total_tokens += chunk_tokens
            
            context = "\n\n---\n\n".join(context_parts)
            
            logger.info(
                "Context retrieved successfully",
                extra={
                    "user_id": user_id,
                    "chunks_count": len(context_parts),
                    "estimated_tokens": total_tokens
                }
            )
            
            return context
            
        except Exception as e:
            logger.error(
                "Context retrieval failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            raise

    async def reset_knowledge_base(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Reset entire knowledge base for a user (delete all data).
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Reset statistics (chunks deleted, embeddings deleted)
            
        Raises:
            Exception: If reset fails
        """
        logger.info(
            "Resetting knowledge base",
            extra={"user_id": user_id}
        )
        
        try:
            # Delete all embeddings (cascades to chunks via FK)
            embeddings_deleted = await self.vector_service.delete_user_embeddings(
                user_id
            )
            
            # Delete all chunks
            chunks_deleted = await self.chunk_repository.delete_by_user(
                user_id
            )
            
            logger.info(
                "Knowledge base reset complete",
                extra={
                    "user_id": user_id,
                    "chunks_deleted": chunks_deleted,
                    "embeddings_deleted": embeddings_deleted
                }
            )
            
            return {
                "user_id": user_id,
                "chunks_deleted": chunks_deleted,
                "embeddings_deleted": embeddings_deleted,
                "reset_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Knowledge base reset failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            raise
