# Database Modes - Local & Supabase

## ✅ Implementation Complete!

The system now supports **both local and Supabase** databases, switchable via environment variable.

## How to Switch

### Local Mode (Default)
```env
DB_MODE=local
```

**Uses:**
- ChromaDB for vector storage (local files)
- SQLite for users (local file)

### Supabase Mode
```env
DB_MODE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

**Uses:**
- Supabase PostgreSQL with pgvector for vector storage
- Supabase PostgreSQL for users

## What Was Changed

### 1. **Config** (`back/config.py`)
- Added `DB_MODE` setting
- Added Supabase configuration options
- Auto-detects mode and initializes accordingly

### 2. **Database** (`back/database.py`)
- Supports both SQLite (local) and PostgreSQL (Supabase)
- Auto-switches based on `DB_MODE`
- Same User model works for both

### 3. **Vector Store** (`back/vector_store_supabase.py`)
- New Supabase vector store using pgvector
- Same interface as local ChromaDB
- Automatic table/index creation
- Dynamic embedding dimension detection

### 4. **RAG Service** (`back/rag_service.py`)
- Auto-selects vector store based on mode
- Same API, works with both modes

### 5. **Requirements** (`back/requirements.txt`)
- Added `psycopg2-binary` for PostgreSQL
- Added `pgvector` for vector support

## Benefits

✅ **Flexible** - Switch between local and cloud
✅ **Vercel-Ready** - Supabase mode works with Vercel
✅ **Same Code** - No code changes needed, just env vars
✅ **Development** - Use local for dev, Supabase for production
✅ **Migration** - Easy to switch when ready

## Testing

1. **Test Local Mode:**
   ```bash
   # .env
   DB_MODE=local
   # Start backend
   python main.py
   ```

2. **Test Supabase Mode:**
   ```bash
   # .env
   DB_MODE=supabase
   SUPABASE_DB_URL=postgresql://...
   # Start backend
   python main.py
   ```

## Next Steps

1. **For Local Development:**
   - Keep `DB_MODE=local`
   - Everything works as before

2. **For Vercel Deployment:**
   - Set up Supabase project
   - Enable pgvector extension
   - Update `.env` with Supabase credentials
   - Set `DB_MODE=supabase`
   - Deploy!

The system is now **fully flexible** and ready for both local and cloud deployment! 🚀
