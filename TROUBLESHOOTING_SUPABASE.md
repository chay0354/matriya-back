# Troubleshooting Supabase Connection Issues

## Common Issues and Solutions

### Issue 1: 400 Bad Request on Signup

**Possible Causes:**
1. Tables not created in Supabase yet
2. Database connection failing
3. Backend still using local mode

**Solution:**
1. **Make sure you ran the SQL in Supabase:**
   - Go to Supabase SQL Editor
   - Run the SQL from `back/supabase_setup_complete.sql`
   - Verify tables exist in Table Editor

2. **Restart the backend:**
   ```bash
   # Stop the current backend (Ctrl+C)
   cd back
   python main.py
   ```

3. **Check backend logs:**
   - Look for "Using Supabase PostgreSQL database"
   - Look for any connection errors

### Issue 2: 500 Internal Server Error on File Upload

**Possible Causes:**
1. pgvector extension not enabled
2. Documents table not created
3. Vector store connection failing

**Solution:**
1. **Enable pgvector:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Create documents table:**
   ```sql
   CREATE TABLE IF NOT EXISTS documents (
       id TEXT PRIMARY KEY,
       embedding vector(384),
       document TEXT NOT NULL,
       metadata JSONB,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Create vector index:**
   ```sql
   CREATE INDEX IF NOT EXISTS documents_embedding_idx 
   ON documents 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

### Issue 3: Backend Still Using Local Mode

**Check:**
1. Verify `.env` file has `DB_MODE=supabase`
2. Restart backend after changing `.env`
3. Check backend startup logs

**Verify .env:**
```bash
cd back
cat .env | grep DB_MODE
# Should show: DB_MODE=supabase
```

### Issue 4: Connection String Issues

**Check connection string format:**
```
postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
```

**Common mistakes:**
- Missing `postgresql://` prefix
- Wrong password
- Wrong host (should be `db.PROJECT.supabase.co`)
- Wrong port (should be `5432`)

### Issue 5: Tables Already Exist Error

If you get "relation already exists":
- That's OK! The `IF NOT EXISTS` should prevent this
- If it still happens, drop and recreate:
  ```sql
  DROP TABLE IF EXISTS users CASCADE;
  DROP TABLE IF EXISTS documents CASCADE;
  -- Then run the setup SQL again
  ```

## Quick Diagnostic Steps

1. **Check backend logs:**
   - Look for database connection messages
   - Look for any error messages

2. **Test connection:**
   ```bash
   cd back
   python -c "from config import settings; print('Mode:', settings.DB_MODE); print('DB URL set:', bool(settings.SUPABASE_DB_URL))"
   ```

3. **Verify Supabase:**
   - Go to Supabase Dashboard
   - Check Table Editor for `users` and `documents` tables
   - Check SQL Editor for any errors

4. **Check .env file:**
   - Make sure `DB_MODE=supabase` (not `local`)
   - Make sure `SUPABASE_DB_URL` is set correctly
   - No extra quotes or spaces

## Still Having Issues?

1. **Check backend terminal output** - it will show the actual error
2. **Check Supabase logs** - Dashboard → Logs
3. **Try switching back to local mode** to verify the system works:
   ```env
   DB_MODE=local
   ```
   Then switch back to supabase after fixing issues.
