-- ============================================================================
-- Admin Setup SQL - Run this in your database (SQLite or Supabase)
-- ============================================================================

-- Step 1: Create file_permissions table (if not exists)
-- This table stores which files each user can access
CREATE TABLE IF NOT EXISTS file_permissions (
    id SERIAL PRIMARY KEY,  -- Use INTEGER PRIMARY KEY AUTOINCREMENT for SQLite
    user_id INTEGER NOT NULL,
    filename VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS file_permissions_user_id_idx ON file_permissions(user_id);
CREATE INDEX IF NOT EXISTS file_permissions_filename_idx ON file_permissions(filename);

-- Step 2: Create admin user (if doesn't exist)
-- Option A: If you're using Supabase PostgreSQL
-- First, check if admin user exists, if not, create it
-- You'll need to hash the password first using bcrypt
-- Default password: "admin123" (CHANGE THIS!)

-- For PostgreSQL (Supabase):
-- The password hash for "admin123" using bcrypt is approximately:
-- $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5Y
-- But you should generate your own hash or use the signup endpoint

-- Option B: Use the signup endpoint to create admin user
-- POST /auth/signup with:
-- {
--   "username": "admin",
--   "email": "admin@example.com",
--   "password": "your_secure_password",
--   "full_name": "Admin User"
-- }
-- Then update the user to set is_admin = true

-- Step 3: Set existing user as admin (if username is "admin")
UPDATE users 
SET is_admin = TRUE 
WHERE username = 'admin';

-- OR set a specific user as admin by ID:
-- UPDATE users SET is_admin = TRUE WHERE id = 1;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check if file_permissions table exists:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_name = 'file_permissions';

-- Check admin users:
-- SELECT id, username, email, is_admin FROM users WHERE is_admin = TRUE OR username = 'admin';

-- Check file permissions:
-- SELECT * FROM file_permissions;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. For SQLite: Replace SERIAL with INTEGER PRIMARY KEY AUTOINCREMENT
-- 2. For password hashing: Use the /auth/signup endpoint or bcrypt directly
-- 3. The admin user can be created via the signup endpoint, then set is_admin = TRUE
-- 4. Default behavior: Users with no file_permissions entries can access all files
-- 5. Users with specific file_permissions can only access those files
