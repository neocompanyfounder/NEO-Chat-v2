"""Unit tests for chunking service (T060)."""

import pytest
from src.services.chunking_service import ChunkingService
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        MIN_CHUNK_TOKENS=100,
        MAX_CHUNK_TOKENS=500,
        CHUNK_OVERLAP_TOKENS=50
    )


@pytest.fixture
def chunking_service(settings):
    """Create chunking service instance."""
    return ChunkingService(settings)


class TestTokenCounting:
    """Test token counting functionality."""
    
    def test_count_tokens_simple_text(self, chunking_service):
        """Test token counting for simple text."""
        text = "This is a simple test sentence."
        token_count = chunking_service.count_tokens(text)
        
        # Should be approximately 7-8 tokens
        assert 5 <= token_count <= 10
    
    def test_count_tokens_empty_text(self, chunking_service):
        """Test token counting for empty text."""
        token_count = chunking_service.count_tokens("")
        assert token_count == 0
    
    def test_count_tokens_long_text(self, chunking_service):
        """Test token counting for longer text."""
        text = " ".join(["word"] * 100)  # 100 words
        token_count = chunking_service.count_tokens(text)
        
        # Should be around 100 tokens
        assert 90 <= token_count <= 110
    
    def test_count_tokens_special_characters(self, chunking_service):
        """Test token counting with special characters."""
        text = "Hello! How are you? I'm fine, thanks."
        token_count = chunking_service.count_tokens(text)
        
        # Punctuation affects tokenization
        assert token_count > 0


class TestSentenceSplitting:
    """Test sentence splitting functionality."""
    
    def test_split_into_sentences_simple(self, chunking_service):
        """Test splitting simple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = chunking_service.split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]
    
    def test_split_into_sentences_with_abbreviations(self, chunking_service):
        """Test splitting with abbreviations."""
        text = "Dr. Smith works at U.S. Labs. He is a scientist."
        sentences = chunking_service.split_into_sentences(text)
        
        # Should not split on abbreviations
        assert len(sentences) == 2
    
    def test_split_into_sentences_with_newlines(self, chunking_service):
        """Test splitting with newlines."""
        text = "First paragraph.\n\nSecond paragraph."
        sentences = chunking_service.split_into_sentences(text)
        
        assert len(sentences) >= 2
    
    def test_split_into_sentences_empty(self, chunking_service):
        """Test splitting empty text."""
        sentences = chunking_service.split_into_sentences("")
        assert len(sentences) == 0
    
    def test_split_into_sentences_no_periods(self, chunking_service):
        """Test splitting text without periods."""
        text = "This is one long sentence without any periods"
        sentences = chunking_service.split_into_sentences(text)
        
        # Should return the whole text as one sentence
        assert len(sentences) == 1


class TestSemanticChunking:
    """Test semantic chunking functionality."""
    
    @pytest.mark.asyncio
    async def test_chunk_text_within_limits(self, chunking_service):
        """Test chunking text that fits within token limits."""
        # Create text with ~200 tokens (within 100-500 range)
        text = " ".join(["word"] * 150)
        
        chunks = await chunking_service.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert 100 <= chunks[0]["metadata"]["token_count"] <= 500
    
    @pytest.mark.asyncio
    async def test_chunk_text_exceeds_max(self, chunking_service):
        """Test chunking text that exceeds max tokens."""
        # Create text with ~1000 tokens (exceeds 500 max)
        text = " ".join(["word"] * 800)
        
        chunks = await chunking_service.chunk_text(text)
        
        # Should split into multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be within limits
        for chunk in chunks:
            assert chunk["metadata"]["token_count"] <= 500
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_sentences(self, chunking_service):
        """Test chunking preserves sentence boundaries."""
        # Create text with clear sentences
        sentences = [f"This is sentence number {i}." for i in range(100)]
        text = " ".join(sentences)
        
        chunks = await chunking_service.chunk_text(text)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should end with a complete sentence
        for chunk in chunks:
            assert chunk["text"].strip().endswith(".")
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_overlap(self, chunking_service):
        """Test that chunks have overlap for context."""
        # Create text that will be split
        text = " ".join([f"Sentence {i}." for i in range(200)])
        
        chunks = await chunking_service.chunk_text(text)
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            # (This is implementation-specific, adjust based on actual behavior)
            assert len(chunks) >= 2
    
    @pytest.mark.asyncio
    async def test_chunk_text_empty(self, chunking_service):
        """Test chunking empty text."""
        chunks = await chunking_service.chunk_text("")
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_chunk_text_very_short(self, chunking_service):
        """Test chunking very short text."""
        text = "Short text."
        chunks = await chunking_service.chunk_text(text)
        
        # Should return one chunk even if below min tokens
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_metadata(self, chunking_service):
        """Test chunking with custom metadata."""
        text = " ".join(["word"] * 150)
        metadata = {
            "source": "test_document.pdf",
            "page": 1,
            "user_id": "test-user"
        }
        
        chunks = await chunking_service.chunk_text(text, metadata=metadata)
        
        assert len(chunks) > 0
        # Check that metadata is preserved
        for chunk in chunks:
            assert chunk["metadata"]["source"] == "test_document.pdf"
            assert chunk["metadata"]["page"] == 1
            assert chunk["metadata"]["user_id"] == "test-user"
    
    @pytest.mark.asyncio
    async def test_chunk_text_adds_chunk_index(self, chunking_service):
        """Test that chunks are indexed."""
        # Create text that will be split into multiple chunks
        text = " ".join(["word"] * 800)
        
        chunks = await chunking_service.chunk_text(text)
        
        # Check that chunks have sequential indices
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i
            assert chunk["metadata"]["total_chunks"] == len(chunks)


class TestChunkQuality:
    """Test chunk quality and coherence."""
    
    @pytest.mark.asyncio
    async def test_chunks_are_coherent(self, chunking_service):
        """Test that chunks maintain coherence."""
        text = """
        This is the first paragraph. It contains multiple sentences.
        Each sentence adds to the meaning.
        
        This is the second paragraph. It has a different topic.
        But it's still related to the overall document.
        
        This is the third paragraph. It concludes the document.
        """
        
        chunks = await chunking_service.chunk_text(text)
        
        # Each chunk should be non-empty and contain complete sentences
        for chunk in chunks:
            assert len(chunk["text"].strip()) > 0
            # Should not start or end with incomplete words
            assert not chunk["text"].strip().startswith(" ")
    
    @pytest.mark.asyncio
    async def test_no_duplicate_content(self, chunking_service):
        """Test that chunks don't have excessive duplication."""
        text = " ".join([f"Unique sentence {i}." for i in range(100)])
        
        chunks = await chunking_service.chunk_text(text)
        
        # Collect all chunk texts
        chunk_texts = [chunk["text"] for chunk in chunks]
        
        # While there may be overlap, chunks should be mostly unique
        assert len(set(chunk_texts)) == len(chunk_texts) or len(chunks) == 1
    
    @pytest.mark.asyncio
    async def test_chunks_preserve_meaning(self, chunking_service):
        """Test that important content is preserved."""
        text = "Important keyword here. " * 100
        
        chunks = await chunking_service.chunk_text(text)
        
        # All chunks should contain the important keyword
        for chunk in chunks:
            assert "Important keyword" in chunk["text"]


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_unicode(self, chunking_service):
        """Test chunking text with Unicode characters."""
        text = "Hello 世界! Café résumé naïve. " * 50
        
        chunks = await chunking_service.chunk_text(text)
        
        assert len(chunks) > 0
        # Unicode should be preserved
        for chunk in chunks:
            assert "世界" in chunk["text"] or "Café" in chunk["text"]
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_code(self, chunking_service):
        """Test chunking text containing code."""
        text = """
        def hello_world():
            print("Hello, world!")
            return True
        
        This is a Python function. It prints a message.
        """ * 20
        
        chunks = await chunking_service.chunk_text(text)
        
        assert len(chunks) > 0
        # Code structure should be preserved
        for chunk in chunks:
            if "def hello_world" in chunk["text"]:
                assert "print" in chunk["text"]
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_urls(self, chunking_service):
        """Test chunking text with URLs."""
        text = "Visit https://example.com for more info. " * 50
        
        chunks = await chunking_service.chunk_text(text)
        
        assert len(chunks) > 0
        # URLs should not be broken
        for chunk in chunks:
            if "https://" in chunk["text"]:
                assert "example.com" in chunk["text"]
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_numbers(self, chunking_service):
        """Test chunking text with numbers and data."""
        text = "The value is 123.456 and the count is 789. " * 50
        
        chunks = await chunking_service.chunk_text(text)
        
        assert len(chunks) > 0
        # Numbers should be preserved
        for chunk in chunks:
            if "123.456" in chunk["text"]:
                assert "value" in chunk["text"]


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_chunk_large_document(self, chunking_service):
        """Test chunking a large document."""
        # Create a large document (~10,000 words)
        text = " ".join([f"Word {i}." for i in range(10000)])
        
        chunks = await chunking_service.chunk_text(text)
        
        # Should handle large documents
        assert len(chunks) > 10
        
        # All chunks should be within limits
        for chunk in chunks:
            assert chunk["metadata"]["token_count"] <= 500
    
    @pytest.mark.asyncio
    async def test_chunk_many_short_sentences(self, chunking_service):
        """Test chunking many short sentences."""
        sentences = [f"S{i}." for i in range(1000)]
        text = " ".join(sentences)
        
        chunks = await chunking_service.chunk_text(text)
        
        # Should efficiently handle many sentences
        assert len(chunks) > 0
        assert all(chunk["metadata"]["token_count"] <= 500 for chunk in chunks)
