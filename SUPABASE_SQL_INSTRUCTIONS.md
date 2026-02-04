# Supabase SQL Setup Instructions

## Quick Steps

### 1. Open Supabase SQL Editor

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project: `tymorwyygffvruqdtwal`
3. Click on **"SQL Editor"** in the left sidebar
4. Click **"New query"**

### 2. Copy and Paste the SQL

Copy the entire contents of `back/supabase_setup_complete.sql` and paste it into the SQL Editor.

### 3. Run the SQL

Click the **"Run"** button (or press `Ctrl+Enter` / `Cmd+Enter`)

### 4. Verify Success

You should see:
- ✅ "Success. No rows returned" (this is normal)
- Or check the Table Editor to see the new tables

## What Gets Created

### Tables:
1. **`users`** - For user authentication
   - Stores usernames, emails, passwords, etc.
   
2. **`documents`** - For vector storage
   - Stores document text, embeddings, metadata
   - Uses pgvector for similarity search

### Indexes:
- `users_username_idx` - Fast username lookups
- `users_email_idx` - Fast email lookups
- `documents_embedding_idx` - Fast vector similarity search
- `documents_metadata_idx` - Fast metadata filtering
- `documents_metadata_filename_idx` - Fast filename filtering

## Alternative: Run Step by Step

If you prefer to run commands one at a time:

### Step 1: Enable pgvector
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 2: Create users table
```sql
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
```

### Step 3: Create documents table
```sql
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    embedding vector(384),
    document TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step 4: Create indexes
```sql
CREATE INDEX IF NOT EXISTS users_username_idx ON users(username);
CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING GIN (metadata);
CREATE INDEX IF NOT EXISTS documents_metadata_filename_idx 
ON documents USING BTREE ((metadata->>'filename'));
```

## Verify Tables Were Created

Go to **Table Editor** in Supabase Dashboard and you should see:
- ✅ `users` table
- ✅ `documents` table

## After Running SQL

1. **Restart your backend:**
   ```bash
   cd back
   python main.py
   ```

2. **Test it:**
   - Sign up a new user (should create a row in `users` table)
   - Upload a document (should create rows in `documents` table)
   - Search documents (should query `documents` table)

## Troubleshooting

### Error: "extension vector does not exist"
- Make sure you're running the SQL in the correct Supabase project
- Try running `CREATE EXTENSION vector;` first

### Error: "permission denied"
- Make sure you're using the correct database credentials
- Check that your user has CREATE privileges

### Tables already exist
- That's OK! The `IF NOT EXISTS` clauses prevent errors
- You can verify tables exist in Table Editor

## Done!

Once you've run the SQL, your Supabase database is ready to use! 🚀
