# Supabase Quick Start

## ✅ Your Supabase is Configured!

Your `.env` file has been updated with your Supabase credentials.

## Next Steps

### 1. Enable pgvector Extension

Go to your Supabase Dashboard → SQL Editor and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Or use the provided file:
```bash
# Copy the SQL from back/setup_supabase.sql
# Paste it in Supabase SQL Editor
```

### 2. Install PostgreSQL Dependencies

```bash
cd back
pip install psycopg2-binary pgvector
```

### 3. Restart Backend

The system will automatically:
- Connect to Supabase PostgreSQL
- Create the `users` table (for authentication)
- Create the `documents` table with pgvector (for vector storage)
- Create necessary indexes

### 4. Test the Connection

```bash
cd back
python main.py
```

You should see:
```
Using Supabase PostgreSQL database
Database tables initialized successfully
```

## Your Configuration

- **Mode**: Supabase
- **URL**: https://tymorwyygffvruqdtwal.supabase.co
- **Database**: PostgreSQL with pgvector
- **Users**: Stored in Supabase PostgreSQL
- **Vectors**: Stored in Supabase PostgreSQL with pgvector

## Switching Back to Local

If you want to switch back to local mode:

```env
DB_MODE=local
# Comment out or remove Supabase settings
```

## Troubleshooting

### Connection Issues
- Verify the password is correct
- Check if your IP is allowed in Supabase (Settings → Database → Connection Pooling)
- Try using the non-pooling connection string if pooling fails

### pgvector Not Found
- Make sure you ran `CREATE EXTENSION IF NOT EXISTS vector;` in SQL Editor
- Check Supabase project settings to ensure extensions are enabled

### Tables Not Created
- The tables are created automatically on first run
- Check Supabase Dashboard → Table Editor to verify
- Check backend logs for any errors

## Ready for Vercel!

Now that you're using Supabase, you can deploy to Vercel:
- Frontend: Vercel
- Backend: Vercel (serverless functions) or Railway/Render
- Database: Supabase ✅

Everything is configured and ready! 🚀
