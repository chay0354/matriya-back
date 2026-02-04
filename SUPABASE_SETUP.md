# Supabase Setup Guide

## Overview

The system now supports both **local** and **Supabase** databases. You can switch between them using the `DB_MODE` environment variable.

## Database Modes

### Local Mode (`DB_MODE=local`)
- **Vector DB**: ChromaDB (local files)
- **User DB**: SQLite (local file)
- **Best for**: Development, offline use, small deployments

### Supabase Mode (`DB_MODE=supabase`)
- **Vector DB**: Supabase PostgreSQL with pgvector
- **User DB**: Supabase PostgreSQL
- **Best for**: Production, cloud deployment, Vercel compatibility

## Setting Up Supabase

### 1. Create Supabase Project

1. Go to https://supabase.com
2. Create a new project
3. Wait for project to be ready

### 2. Enable pgvector Extension

In Supabase SQL Editor, run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Get Connection Details

From Supabase Dashboard → Settings → Database:

1. **Connection String**: 
   - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`
   - Replace `[PASSWORD]` with your database password
   - Replace `[PROJECT]` with your project reference

2. **API URL**: `https://[PROJECT].supabase.co`
3. **Anon Key**: From Settings → API

### 4. Update `.env` File

```env
DB_MODE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### 5. Restart Backend

The system will automatically:
- Use Supabase PostgreSQL for users
- Use Supabase pgvector for document embeddings
- Create necessary tables and indexes

## Switching Between Modes

### Switch to Supabase:
```env
DB_MODE=supabase
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_DB_URL=...
```

### Switch to Local:
```env
DB_MODE=local
# Remove or comment out Supabase settings
```

## Migration Notes

- **Data Migration**: When switching modes, you'll need to re-upload documents
- **Users**: User accounts are separate between modes
- **No Data Loss**: Local data stays in local files, Supabase data stays in cloud

## Benefits of Supabase Mode

✅ **Cloud-hosted** - No local files
✅ **Scalable** - Handles large datasets
✅ **Vercel-compatible** - Works with serverless
✅ **Managed** - Automatic backups, monitoring
✅ **Real-time** - Optional real-time subscriptions

## Benefits of Local Mode

✅ **Fully offline** - No internet needed
✅ **Fast** - No network latency
✅ **Private** - All data stays local
✅ **Free** - No cloud costs
✅ **Simple** - No setup required

## Testing

After switching modes, test:
1. User signup/login
2. Document upload
3. Document search
4. File selection

Both modes should work identically from the user's perspective!
