"""Integration tests for Supabase vector database integration.

Tests the vector service integration with Supabase for vector operations.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.vector_service import VectorService
from src.utils.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        EVOLUTION_API_URL="http://test-evolution-api:8080",
        EVOLUTION_API_KEY="test-api-key",
        EVOLUTION_INSTANCE_NAME="test-instance",
        EVOLUTION_TIMEOUT=10,
        GOOGLE_API_KEY="test-google-key",
        GEMINI_MODEL="gemini-2.0-flash-exp",
        GEMINI_EMBEDDING_MODEL="text-embedding-004",
        GEMINI_TIMEOUT=30,
        SUPABASE_URL="postgresql://test:test@localhost:5432/test",
        SUPABASE_SERVICE_ROLE_KEY="test-service-key",
        SUPABASE_ANON_KEY="test-anon-key",
        SUPABASE_TIMEOUT=5,
        APP_ENV="test",
        LOG_LEVEL="DEBUG",
        MAX_FILE_SIZE_MB=16,
        MAX_CONCURRENT_USERS=100,
        GEMINI_RATE_LIMIT_PER_MIN=60,
        WHATSAPP_RATE_LIMIT_PER_MIN=60,
        MAX_RETRIES=5,
        RETRY_BACKOFF_BASE=1,
        VECTOR_SIMILARITY_THRESHOLD=0.7,
        VECTOR_TOP_K=5,
        MAX_CONTEXT_TOKENS=8000,
        MIN_CHUNK_TOKENS=100,
        MAX_CHUNK_TOKENS=2000,
        MAX_CRAWL_PAGES=100,
        CRAWL_TIMEOUT_MINUTES=5,
        CRAWL_RATE_LIMIT_SECONDS=1
    )


@pytest.fixture
def vector_service(settings):
    """Create vector service instance."""
    return VectorService(settings)


@pytest.mark.asyncio
class TestSupabaseIntegration:
    """Integration tests for Supabase vector service."""
    
    async def test_store_embedding_success(self, vector_service):
        """Test storing an embedding successfully."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "INSERT 1"
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Store embedding
            embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
            result = await vector_service.store_embedding(
                user_id="test-user-123",
                chunk_id="chunk-456",
                embedding=embedding,
                metadata={"source": "test"}
            )
            
            # Verify
            assert result is True
            mock_conn.execute.assert_called_once()
    
    async def test_store_embedding_invalid_dimensions(self, vector_service):
        """Test storing embedding with invalid dimensions."""
        with pytest.raises(ValueError, match="Embedding must have 768 dimensions"):
            embedding = [0.1, 0.2, 0.3]  # Wrong dimensions
            await vector_service.store_embedding(
                user_id="test-user-123",
                chunk_id="chunk-456",
                embedding=embedding,
                metadata={}
            )
    
    async def test_search_similar_chunks_success(self, vector_service):
        """Test searching for similar chunks successfully."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [
                {
                    "chunk_id": "chunk-1",
                    "content": "Test content 1",
                    "similarity": 0.95,
                    "metadata": {"source": "doc1"}
                },
                {
                    "chunk_id": "chunk-2",
                    "content": "Test content 2",
                    "similarity": 0.85,
                    "metadata": {"source": "doc2"}
                },
                {
                    "chunk_id": "chunk-3",
                    "content": "Test content 3",
                    "similarity": 0.75,
                    "metadata": {"source": "doc3"}
                }
            ]
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Search for similar chunks
            query_embedding = [0.1, 0.2, 0.3] * 256
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=query_embedding,
                top_k=5,
                threshold=0.7
            )
            
            # Verify
            assert len(results) == 3
            assert all(r["similarity"] >= 0.7 for r in results)
            assert results[0]["similarity"] >= results[1]["similarity"]
            mock_conn.fetch.assert_called_once()
    
    async def test_search_similar_chunks_no_results(self, vector_service):
        """Test searching with no results above threshold."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection with no results
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = []
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Search for similar chunks
            query_embedding = [0.1, 0.2, 0.3] * 256
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=query_embedding,
                top_k=5,
                threshold=0.9  # High threshold
            )
            
            # Verify
            assert len(results) == 0
    
    async def test_search_similar_chunks_with_retry(self, vector_service):
        """Test vector search with retry on failure."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock failure then success
            mock_conn = AsyncMock()
            mock_conn.fetch.side_effect = [
                Exception("Connection lost"),
                [
                    {
                        "chunk_id": "chunk-1",
                        "content": "Test content",
                        "similarity": 0.85,
                        "metadata": {}
                    }
                ]
            ]
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Search (should retry)
            query_embedding = [0.1, 0.2, 0.3] * 256
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=query_embedding,
                top_k=5,
                threshold=0.7
            )
            
            # Verify retry worked
            assert len(results) == 1
            assert mock_conn.fetch.call_count == 2
    
    async def test_delete_user_embeddings_success(self, vector_service):
        """Test deleting all embeddings for a user."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "DELETE 10"
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Delete embeddings
            result = await vector_service.delete_user_embeddings(
                user_id="test-user-123"
            )
            
            # Verify
            assert result is True
            mock_conn.execute.assert_called_once()
    
    async def test_get_embedding_count_success(self, vector_service):
        """Test getting embedding count for a user."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = 42
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Get count
            count = await vector_service.get_embedding_count(
                user_id="test-user-123"
            )
            
            # Verify
            assert count == 42
            mock_conn.fetchval.assert_called_once()
    
    async def test_hnsw_index_performance(self, vector_service):
        """Test HNSW index performance for vector search."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            
            # Simulate large result set
            mock_results = [
                {
                    "chunk_id": f"chunk-{i}",
                    "content": f"Content {i}",
                    "similarity": 0.9 - (i * 0.01),
                    "metadata": {}
                }
                for i in range(100)
            ]
            mock_conn.fetch.return_value = mock_results[:5]  # Top 5
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Search with HNSW index
            query_embedding = [0.1, 0.2, 0.3] * 256
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=query_embedding,
                top_k=5,
                threshold=0.7
            )
            
            # Verify
            assert len(results) == 5
            assert all(r["similarity"] >= 0.7 for r in results)
    
    async def test_connection_pool_management(self, vector_service):
        """Test connection pool management."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock multiple connections
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = []
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Make multiple concurrent requests
            query_embedding = [0.1, 0.2, 0.3] * 256
            
            tasks = []
            for i in range(10):
                task = vector_service.search_similar_chunks(
                    user_id=f"user-{i}",
                    query_embedding=query_embedding,
                    top_k=5,
                    threshold=0.7
                )
                tasks.append(task)
            
            # Execute concurrently
            import asyncio
            results = await asyncio.gather(*tasks)
            
            # Verify all completed
            assert len(results) == 10
    
    async def test_vector_similarity_threshold(self, vector_service):
        """Test vector similarity threshold filtering."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection with varied similarities
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [
                {"chunk_id": "1", "content": "High", "similarity": 0.95, "metadata": {}},
                {"chunk_id": "2", "content": "Medium", "similarity": 0.75, "metadata": {}},
                {"chunk_id": "3", "content": "Low", "similarity": 0.65, "metadata": {}}
            ]
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Search with threshold 0.7
            query_embedding = [0.1, 0.2, 0.3] * 256
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=query_embedding,
                top_k=5,
                threshold=0.7
            )
            
            # Verify only results above threshold
            assert len(results) == 2  # 0.95 and 0.75, not 0.65
            assert all(r["similarity"] >= 0.7 for r in results)
    
    async def test_metadata_storage_and_retrieval(self, vector_service):
        """Test storing and retrieving metadata with embeddings."""
        with patch.object(vector_service.client, 'acquire') as mock_acquire:
            # Mock database connection
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = "INSERT 1"
            mock_conn.fetch.return_value = [
                {
                    "chunk_id": "chunk-1",
                    "content": "Test content",
                    "similarity": 0.9,
                    "metadata": {
                        "source": "document.pdf",
                        "page": 5,
                        "timestamp": "2025-01-17T10:00:00Z"
                    }
                }
            ]
            mock_acquire.return_value.__aenter__.return_value = mock_conn
            
            # Store with metadata
            embedding = [0.1, 0.2, 0.3] * 256
            await vector_service.store_embedding(
                user_id="test-user-123",
                chunk_id="chunk-1",
                embedding=embedding,
                metadata={
                    "source": "document.pdf",
                    "page": 5,
                    "timestamp": "2025-01-17T10:00:00Z"
                }
            )
            
            # Search and verify metadata
            results = await vector_service.search_similar_chunks(
                user_id="test-user-123",
                query_embedding=embedding,
                top_k=1,
                threshold=0.7
            )
            
            assert len(results) == 1
            assert results[0]["metadata"]["source"] == "document.pdf"
            assert results[0]["metadata"]["page"] == 5
