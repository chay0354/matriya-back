-- ============================================================================
-- Supabase Setup SQL - Run this in Supabase SQL Editor
-- ============================================================================

-- Step 1: Enable pgvector extension (REQUIRED for vector storage)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Step 3: Create indexes for users table (for faster lookups)
CREATE INDEX IF NOT EXISTS users_username_idx ON users(username);
CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);

-- Step 4: Create documents table (for vector storage)
-- Note: The embedding dimension (384) matches all-MiniLM-L6-v2 model
-- If you use a different model, change the dimension accordingly
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    embedding vector(384),
    document TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 5: Create vector index for similarity search (IMPORTANT for performance)
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 6: Create index on metadata for faster filtering
CREATE INDEX IF NOT EXISTS documents_metadata_idx 
ON documents 
USING GIN (metadata);

-- Step 7: Create index on metadata->filename for file filtering
CREATE INDEX IF NOT EXISTS documents_metadata_filename_idx 
ON documents 
USING BTREE ((metadata->>'filename'));

-- ============================================================================
-- Verification Queries (optional - run to check everything is set up)
-- ============================================================================

-- Check if pgvector is enabled:
-- SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check if tables exist:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' AND table_name IN ('users', 'documents');

-- Check if indexes exist:
-- SELECT indexname FROM pg_indexes 
-- WHERE tablename IN ('users', 'documents');

-- ============================================================================
-- Done! Your tables are ready.
-- ============================================================================
