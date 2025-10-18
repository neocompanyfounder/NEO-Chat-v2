"""Chunking service for semantic text chunking.

This module provides semantic chunking of text into manageable pieces
for embedding and vector storage (100-2000 tokens per chunk).
"""

import re
from typing import List, Dict, Any
from src.utils.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChunkingService:
    """Service for semantic text chunking."""
    
    def __init__(self, settings: Settings):
        """Initialize chunking service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.min_tokens = settings.MIN_CHUNK_TOKENS
        self.max_tokens = settings.MAX_CHUNK_TOKENS
        
        # Approximate tokens per character (rough estimate)
        # More accurate would be to use tiktoken, but this is simpler
        self.chars_per_token = 4
        
        logger.info(
            "Chunking service initialized",
            extra={
                "min_tokens": self.min_tokens,
                "max_tokens": self.max_tokens
            }
        )
    
    async def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text into semantic pieces.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunks with text and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        metadata = metadata or {}
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        # Create chunks from paragraphs
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            
            # If single paragraph exceeds max tokens, split it further
            if para_tokens > self.max_tokens:
                # Flush current chunk if it has content
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph into sentences
                sentences = self._split_into_sentences(para)
                for sentence in sentences:
                    sentence_tokens = self._estimate_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > self.max_tokens:
                        if current_chunk:
                            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                        current_chunk = [sentence]
                        current_tokens = sentence_tokens
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens
            
            # If adding paragraph would exceed max, start new chunk
            elif current_tokens + para_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                current_chunk = [para]
                current_tokens = para_tokens
            
            # Add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
            
            # If current chunk meets minimum size, consider it complete
            if current_tokens >= self.min_tokens and current_tokens <= self.max_tokens:
                chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                current_chunk = []
                current_tokens = 0
        
        # Add remaining content as final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
        
        logger.info(
            f"Created {len(chunks)} chunks from text",
            extra={
                "chunks_count": len(chunks),
                "text_length": len(text),
                "avg_chunk_size": sum(len(c["text"]) for c in chunks) // len(chunks) if chunks else 0
            }
        )
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean up and filter empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on common punctuation
        # This is a basic implementation; for production, consider using nltk or spacy
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        This is a rough estimate. For production, consider using tiktoken
        for accurate token counting with the specific model's tokenizer.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // self.chars_per_token
    
    def _create_chunk(
        self,
        content_parts: List[str],
        metadata: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """Create a chunk dictionary.
        
        Args:
            content_parts: List of text parts to combine
            metadata: Metadata to attach
            chunk_index: Index of this chunk
            
        Returns:
            Chunk dictionary
        """
        text = "\n\n".join(content_parts)
        
        chunk_metadata = {
            **metadata,
            "chunk_index": chunk_index,
            "token_count": self._estimate_tokens(text),
            "char_count": len(text)
        }
        
        return {
            "text": text,
            "metadata": chunk_metadata
        }
    
    async def chunk_document(
        self,
        document_text: str,
        document_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk a document with its metadata.
        
        This is a convenience method that adds document-specific metadata
        to each chunk.
        
        Args:
            document_text: Full document text
            document_metadata: Document metadata (filename, type, etc.)
            
        Returns:
            List of chunks with document metadata
        """
        # Add document info to metadata
        chunk_metadata = {
            "source": "document",
            "document_id": document_metadata.get("document_id"),
            "filename": document_metadata.get("filename"),
            "file_type": document_metadata.get("file_type"),
            **document_metadata
        }
        
        return await self.chunk_text(document_text, chunk_metadata)
    
    async def chunk_conversation(
        self,
        conversation_text: str,
        user_id: str,
        conversation_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Chunk a conversation with user context.
        
        Args:
            conversation_text: Conversation text
            user_id: User identifier
            conversation_metadata: Optional conversation metadata
            
        Returns:
            List of chunks with conversation metadata
        """
        metadata = {
            "source": "conversation",
            "user_id": user_id,
            **(conversation_metadata or {})
        }
        
        return await self.chunk_text(conversation_text, metadata)
    
    def validate_chunk_size(self, text: str) -> bool:
        """Validate if text is within acceptable chunk size.
        
        Args:
            text: Text to validate
            
        Returns:
            True if within limits, False otherwise
        """
        tokens = self._estimate_tokens(text)
        return self.min_tokens <= tokens <= self.max_tokens
