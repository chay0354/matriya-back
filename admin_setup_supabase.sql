-- ============================================================================
-- Admin Setup SQL for Supabase PostgreSQL
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Step 1: Create file_permissions table
CREATE TABLE IF NOT EXISTS file_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    filename VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS file_permissions_user_id_idx ON file_permissions(user_id);
CREATE INDEX IF NOT EXISTS file_permissions_filename_idx ON file_permissions(filename);

-- Step 2: Set existing user as admin (if username is "admin")
UPDATE users 
SET is_admin = TRUE 
WHERE username = 'admin';

-- ============================================================================
-- To create admin user:
-- ============================================================================
-- Option 1: Use the signup endpoint: POST /auth/signup
-- {
--   "username": "admin",
--   "email": "admin@example.com",
--   "password": "your_secure_password",
--   "full_name": "Admin User"
-- }
-- 
-- Then run: UPDATE users SET is_admin = TRUE WHERE username = 'admin';
--
-- Option 2: Create directly in database (requires password hashing):
-- INSERT INTO users (username, email, hashed_password, is_admin)
-- VALUES ('admin', 'admin@example.com', '$2b$12$...', TRUE);
-- (You need to generate the bcrypt hash for your password)
