-- Migration 004: Create crawl_jobs table for web crawling (User Story 3)
-- This table tracks web crawling jobs, their status, and progress

-- Create crawl_jobs table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    max_depth INTEGER NOT NULL DEFAULT 3 CHECK (max_depth >= 0 AND max_depth <= 10),
    max_pages INTEGER NOT NULL DEFAULT 100 CHECK (max_pages >= 1 AND max_pages <= 1000),
    respect_robots BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'pending',
    pages_crawled INTEGER DEFAULT 0 CHECK (pages_crawled >= 0),
    pages_found INTEGER DEFAULT 0 CHECK (pages_found >= 0),
    chunks_created INTEGER DEFAULT 0 CHECK (chunks_created >= 0),
    error_message TEXT,
    failed_urls TEXT[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'crawling', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_timestamps CHECK (
        (started_at IS NULL OR started_at >= created_at) AND
        (completed_at IS NULL OR (started_at IS NOT NULL AND completed_at >= started_at))
    )
);

-- Create indexes for efficient querying
CREATE INDEX idx_crawl_jobs_user_id ON crawl_jobs(user_id);
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
CREATE INDEX idx_crawl_jobs_url ON crawl_jobs(url);
CREATE INDEX idx_crawl_jobs_user_status ON crawl_jobs(user_id, status);

-- Add comments for documentation
COMMENT ON TABLE crawl_jobs IS 'Tracks web crawling jobs for User Story 3';
COMMENT ON COLUMN crawl_jobs.id IS 'Unique identifier for the crawl job';
COMMENT ON COLUMN crawl_jobs.user_id IS 'User who initiated the crawl';
COMMENT ON COLUMN crawl_jobs.url IS 'Starting URL for the crawl';
COMMENT ON COLUMN crawl_jobs.max_depth IS 'Maximum depth to crawl (0-10)';
COMMENT ON COLUMN crawl_jobs.max_pages IS 'Maximum pages to crawl (1-1000)';
COMMENT ON COLUMN crawl_jobs.respect_robots IS 'Whether to respect robots.txt';
COMMENT ON COLUMN crawl_jobs.status IS 'Current status: pending, crawling, completed, failed, cancelled';
COMMENT ON COLUMN crawl_jobs.pages_crawled IS 'Number of pages successfully crawled';
COMMENT ON COLUMN crawl_jobs.pages_found IS 'Total pages discovered (including pending)';
COMMENT ON COLUMN crawl_jobs.chunks_created IS 'Number of content chunks created';
COMMENT ON COLUMN crawl_jobs.error_message IS 'Error message if job failed';
COMMENT ON COLUMN crawl_jobs.failed_urls IS 'Array of URLs that failed to crawl';
COMMENT ON COLUMN crawl_jobs.created_at IS 'When the job was created';
COMMENT ON COLUMN crawl_jobs.started_at IS 'When crawling started';
COMMENT ON COLUMN crawl_jobs.completed_at IS 'When crawling completed (success or failure)';
COMMENT ON COLUMN crawl_jobs.metadata IS 'Additional metadata (domain, duration, etc.)';

-- Grant permissions (adjust based on your database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crawl_jobs TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE crawl_jobs_id_seq TO your_app_user;
