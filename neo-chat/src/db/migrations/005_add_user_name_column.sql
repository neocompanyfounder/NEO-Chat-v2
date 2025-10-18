-- Add name column to users table
-- Migration 005: Add optional name field for user profiles

ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;

-- Create index on name for faster searches
CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);

-- Update schema version
INSERT INTO schema_version (version, description) 
VALUES (5, 'Add name column to users table')
ON CONFLICT (version) DO NOTHING;
