-- Migration 003: Create documents table for file uploads
-- User Story 2: File Upload & Knowledge Base Enrichment

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    mime_type TEXT NOT NULL,
    storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    chunks_count INTEGER DEFAULT 0 CHECK (chunks_count >= 0),
    processing_error TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_file_type CHECK (file_type IN ('pdf', 'docx', 'xlsx', 'pptx', 'txt', 'image', 'unknown'))
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_status ON documents(user_id, status);

-- Add comments for documentation
COMMENT ON TABLE documents IS 'Stores uploaded documents and their processing status';
COMMENT ON COLUMN documents.id IS 'Unique document identifier';
COMMENT ON COLUMN documents.user_id IS 'User who uploaded the document';
COMMENT ON COLUMN documents.filename IS 'Original filename';
COMMENT ON COLUMN documents.file_type IS 'Type of document (pdf, docx, xlsx, pptx, txt, image)';
COMMENT ON COLUMN documents.file_size IS 'File size in bytes';
COMMENT ON COLUMN documents.mime_type IS 'MIME type of the file';
COMMENT ON COLUMN documents.storage_path IS 'Path where file is stored (optional)';
COMMENT ON COLUMN documents.status IS 'Processing status (pending, processing, completed, failed)';
COMMENT ON COLUMN documents.chunks_count IS 'Number of chunks extracted from document';
COMMENT ON COLUMN documents.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN documents.uploaded_at IS 'Timestamp when document was uploaded';
COMMENT ON COLUMN documents.processed_at IS 'Timestamp when processing completed';
COMMENT ON COLUMN documents.metadata IS 'Additional metadata (pages, format, etc.)';

-- Grant permissions (adjust based on your RLS policies)
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY documents_user_policy ON documents FOR ALL USING (auth.uid() = user_id);
