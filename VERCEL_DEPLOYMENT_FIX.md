# Vercel Deployment Fix - 4.3GB Error

## Problem
Vercel is trying to upload 4.3GB during deployment because `sentence-transformers` downloads large model files during installation.

## Solution Applied

1. **Made `sentence-transformers` optional** - The code now works without it
2. **Added API-based embeddings** - Uses Hugging Face Inference API when `sentence-transformers` is not available
3. **Updated `requirements.txt`** - Removed `sentence-transformers` and other large ML libraries
4. **Created `requirements-vercel.txt`** - Minimal dependencies for Vercel

## Vercel Configuration

### Option 1: Use requirements-vercel.txt (Recommended)

In Vercel Dashboard → Your Project → Settings → Build & Development Settings:

1. Set **Install Command** to:
   ```
   pip install -r requirements-vercel.txt
   ```

2. Make sure **DB_MODE=supabase** is set in Environment Variables

3. Make sure **HF_API_TOKEN** is set in Environment Variables (for embeddings API)

### Option 2: Use requirements.txt (Current)

The current `requirements.txt` no longer includes `sentence-transformers`, so it should work. But `requirements-vercel.txt` is safer.

## Environment Variables Required

- `DB_MODE=supabase` (REQUIRED)
- `SUPABASE_DB_URL=...` (REQUIRED)
- `HF_API_TOKEN=...` (REQUIRED for embeddings on Vercel)
- `TOGETHER_API_KEY=...` (for LLM)
- Other Supabase variables as needed

## How It Works

1. **Local Mode**: Uses `sentence-transformers` for embeddings (if installed)
2. **Vercel Mode**: 
   - Detects `VERCEL=1` environment variable
   - Uses Hugging Face Inference API for embeddings
   - Falls back to hash-based embeddings if API fails

## Testing

After deployment, test that:
1. File upload works
2. Search works
3. Embeddings are generated correctly

If embeddings fail, check:
- `HF_API_TOKEN` is set correctly
- Hugging Face API is accessible
- Model name matches: `sentence-transformers/all-MiniLM-L6-v2`
