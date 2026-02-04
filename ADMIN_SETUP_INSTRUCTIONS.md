# Admin Setup Instructions

## Overview
This guide explains how to set up the admin user and file permissions system in your database.

## Step 1: Create file_permissions Table

The `file_permissions` table will be created automatically when you restart the backend (it's defined in `database.py`). However, if you want to create it manually:

### For Supabase (PostgreSQL):
Run the SQL in `back/admin_setup_supabase.sql` in your Supabase SQL Editor.

### For Local SQLite:
Run the SQL in `back/admin_setup_sqlite.sql` using any SQLite client, or it will be created automatically on backend startup.

## Step 2: Create Admin User

### Method 1: Using the Signup Endpoint (Recommended)

1. **Sign up as admin user:**
   ```bash
   POST http://localhost:8000/auth/signup
   {
     "username": "admin",
     "email": "admin@example.com",
     "password": "your_secure_password",
     "full_name": "Admin User"
   }
   ```

2. **Set the user as admin in database:**

   **For Supabase:**
   ```sql
   UPDATE users 
   SET is_admin = TRUE 
   WHERE username = 'admin';
   ```

   **For SQLite:**
   ```sql
   UPDATE users 
   SET is_admin = 1 
   WHERE username = 'admin';
   ```

### Method 2: Direct Database Insert (Advanced)

If you want to create the admin user directly in the database, you'll need to hash the password using bcrypt. This is more complex and not recommended unless you know what you're doing.

## Step 3: Verify Setup

1. **Check if admin user exists:**
   ```sql
   SELECT id, username, email, is_admin 
   FROM users 
   WHERE username = 'admin' OR is_admin = TRUE;
   ```

2. **Check if file_permissions table exists:**
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_name = 'file_permissions';
   ```

3. **Login as admin:**
   - Go to the frontend
   - Login with username "admin" and your password
   - You should see the "ניהול" (Admin) button in the tabs

## How File Permissions Work

- **Default behavior:** Users with NO entries in `file_permissions` table can access ALL files
- **Restricted access:** Users with entries in `file_permissions` can ONLY access the files listed for them
- **Admin access:** Admin users can access all files regardless of permissions

## Admin Features

Once logged in as admin, you can:
1. **View all files** in the database
2. **Delete files** from the database
3. **Manage user permissions:**
   - Set users to access all files
   - Or restrict users to specific files only

## Troubleshooting

### Admin button not showing?
- Check that `user.is_admin === true` or `user.username === 'admin'`
- Verify the user object returned from `/auth/me` includes `is_admin: true`
- Try logging out and logging back in

### Can't access admin endpoints?
- Make sure you're logged in as admin
- Check that the JWT token includes the correct user
- Verify `is_admin` flag in database

### File permissions not working?
- Check that `file_permissions` table exists
- Verify entries in the table are correct
- Default: no entries = access all files
