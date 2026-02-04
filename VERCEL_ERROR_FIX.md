# Vercel 500 Error Fix

## Common Causes

1. **Missing Environment Variables** - Most common cause
2. **Database Connection Issues** - Supabase connection failing
3. **Directory Creation Errors** - Trying to create directories on read-only filesystem
4. **Import Errors** - Missing dependencies or circular imports

## Required Environment Variables

Make sure ALL of these are set in Vercel Dashboard → Settings → Environment Variables:

### Database (REQUIRED)
- `DB_MODE=supabase`
- `SUPABASE_DB_URL=postgres://...` (Full PostgreSQL connection string)

### API Keys (REQUIRED)
- `HF_API_TOKEN=...` (Hugging Face token for embeddings)
- `TOGETHER_API_KEY=...` (Together AI token for LLM)

### Optional
- `CORS_ORIGINS=...` (Comma-separated list of allowed origins)
- `SECRET_KEY=...` (JWT secret key, auto-generated if not set)

## How to Check Logs

1. Go to Vercel Dashboard → Your Project → **Deployments**
2. Click on the failed deployment
3. Click **View Function Logs** or **View Build Logs**
4. Look for the actual error message

## Quick Fixes Applied

1. ✅ Made directory creation optional on Vercel
2. ✅ Made database initialization non-blocking on Vercel
3. ✅ Set `VERCEL=1` environment variable early in `api/index.py`
4. ✅ Fixed duplicate import in `main.py`

## Testing

After setting environment variables, redeploy:
1. Go to Vercel Dashboard → Deployments
2. Click "..." on latest deployment → **Redeploy**

## If Still Failing

Check the function logs for the exact error. Common issues:

- **"SUPABASE_DB_URL must be set"** → Set `DB_MODE=supabase` and `SUPABASE_DB_URL`
- **"Connection refused"** → Check Supabase connection string
- **"Module not found"** → Check `requirements-vercel.txt` is being used
- **"Permission denied"** → Directory creation issue (should be fixed now)
