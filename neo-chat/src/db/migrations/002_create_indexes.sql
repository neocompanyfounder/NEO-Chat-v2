-- NEO Chat Vector Indexes
-- Creates HNSW indexes for efficient vector similarity search

-- HNSW index on embeddings for fast cosine similarity search
-- HNSW (Hierarchical Navigable Small World) is optimal for < 1M vectors
-- Using cosine similarity as specified in FR-017a
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_cosine 
ON embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Additional indexes for performance optimization

-- Composite index for user-specific vector searches
CREATE INDEX IF NOT EXISTS idx_embeddings_user_vector 
ON embeddings(user_id, created_at DESC);

-- Index for document-based queries
CREATE INDEX IF NOT EXISTS idx_chunks_document_user 
ON chunks(document_id, user_id);

-- Index for conversation history queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_created 
ON conversations(user_id, created_at DESC);

-- Partial index for active crawl jobs
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_active 
ON crawl_jobs(user_id, status) 
WHERE status IN ('pending', 'running');

-- GIN index for JSONB metadata in conversations
CREATE INDEX IF NOT EXISTS idx_conversations_metadata 
ON conversations USING gin(metadata);

-- Schema version tracking
INSERT INTO schema_version (version, description) 
VALUES (2, 'HNSW vector indexes and performance optimization indexes')
ON CONFLICT (version) DO NOTHING;

-- Analyze tables for query planner statistics
ANALYZE users;
ANALYZE documents;
ANALYZE chunks;
ANALYZE embeddings;
ANALYZE conversations;
ANALYZE crawl_jobs;
