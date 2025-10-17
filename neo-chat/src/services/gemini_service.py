"""Gemini service for LLM inference and embeddings (T033)."""

import google.generativeai as genai
from typing import Optional, List, Dict, Any
from src.utils.config import Settings
from src.utils.logger import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


class GeminiService:
    """Service for Gemini Flash 2.5 LLM inference and text-embedding-004."""

    def __init__(self, settings: Settings):
        """Initialize Gemini service with API configuration.
        
        Args:
            settings: Application settings containing Gemini API key
        """
        self.settings = settings
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Initialize models
        self.llm_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        
        self.max_context_tokens = settings.MAX_CONTEXT_TOKENS
        self.timeout = settings.GEMINI_TIMEOUT

    @with_retry(max_retries=5, base_delay=1.0)
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate AI response using Gemini Flash 2.5.
        
        Args:
            prompt: User query or prompt
            context: Optional context from knowledge base
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If API call fails
        """
        # Construct full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"""Context from knowledge base:
{context}

User query: {prompt}

Please provide a helpful response based on the context above. If the context doesn't contain relevant information, say so clearly."""
        
        logger.info(
            "Generating Gemini response",
            extra={
                "prompt_length": len(prompt),
                "has_context": bool(context),
                "temperature": temperature
            }
        )
        
        try:
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            response = await self.llm_model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            result_text = response.text
            
            logger.info(
                "Gemini response generated",
                extra={
                    "response_length": len(result_text),
                    "finish_reason": response.candidates[0].finish_reason if response.candidates else None
                }
            )
            
            return result_text
            
        except Exception as e:
            logger.error(
                "Gemini response generation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    @with_retry(max_retries=5, base_delay=1.0)
    async def generate_embedding(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """Generate embedding vector using text-embedding-004.
        
        Args:
            text: Text to embed
            task_type: Task type for embedding (retrieval_document, retrieval_query, etc.)
            
        Returns:
            768-dimensional embedding vector
            
        Raises:
            Exception: If API call fails
        """
        logger.info(
            "Generating embedding",
            extra={
                "text_length": len(text),
                "task_type": task_type
            }
        )
        
        try:
            result = genai.embed_content(
                model=f"models/{self.embedding_model}",
                content=text,
                task_type=task_type
            )
            
            embedding = result['embedding']
            
            logger.info(
                "Embedding generated",
                extra={
                    "dimension": len(embedding),
                    "text_length": len(text)
                }
            )
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Embedding generation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "text_length": len(text)
                }
            )
            raise

    @with_retry(max_retries=5, base_delay=1.0)
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed (max 100 per batch)
            task_type: Task type for embedding
            
        Returns:
            List of 768-dimensional embedding vectors
            
        Raises:
            Exception: If API call fails
        """
        # Limit batch size to 100 per FR-015c
        if len(texts) > 100:
            logger.warning(
                "Batch size exceeds limit, truncating",
                extra={
                    "requested": len(texts),
                    "limit": 100
                }
            )
            texts = texts[:100]
        
        logger.info(
            "Generating batch embeddings",
            extra={
                "batch_size": len(texts),
                "task_type": task_type
            }
        )
        
        try:
            embeddings = []
            for text in texts:
                embedding = await self.generate_embedding(text, task_type)
                embeddings.append(embedding)
            
            logger.info(
                "Batch embeddings generated",
                extra={
                    "batch_size": len(embeddings),
                    "dimension": len(embeddings[0]) if embeddings else 0
                }
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Batch embedding generation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "batch_size": len(texts)
                }
            )
            raise

    async def generate_structured_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate structured response with custom schema (FR-009).
        
        Args:
            prompt: User query or prompt
            context: Optional context from knowledge base
            response_schema: JSON schema for structured output
            
        Returns:
            Structured response matching schema
            
        Raises:
            Exception: If API call fails
        """
        # For MVP, return text response wrapped in dict
        # Full structured output implementation can be added later
        text_response = await self.generate_response(prompt, context)
        
        return {
            "response": text_response,
            "metadata": {
                "model": self.settings.GEMINI_MODEL,
                "has_context": bool(context)
            }
        }
