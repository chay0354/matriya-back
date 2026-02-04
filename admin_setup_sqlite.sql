-- ============================================================================
-- Admin Setup SQL for SQLite (Local Database)
-- ============================================================================

-- Step 1: Create file_permissions table
CREATE TABLE IF NOT EXISTS file_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS file_permissions_user_id_idx ON file_permissions(user_id);
CREATE INDEX IF NOT EXISTS file_permissions_filename_idx ON file_permissions(filename);

-- Step 2: Set existing user as admin (if username is "admin")
UPDATE users 
SET is_admin = 1 
WHERE username = 'admin';

-- ============================================================================
-- To create admin user:
-- ============================================================================
-- Use the signup endpoint: POST /auth/signup
-- {
--   "username": "admin",
--   "email": "admin@example.com",
--   "password": "your_secure_password",
--   "full_name": "Admin User"
-- }
-- 
-- Then run: UPDATE users SET is_admin = 1 WHERE username = 'admin';
