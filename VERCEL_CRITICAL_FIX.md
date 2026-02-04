# CRITICAL: Vercel 4.3GB Error Fix

## The Problem

Vercel is trying to upload 4.3GB during deployment. This is likely because:

1. **Python dependencies** (`sentence-transformers`, `transformers`) download large model files
2. **Vercel cache** contains old large files
3. **Build process** includes files that should be excluded

## Solution Applied

1. ✅ Created `requirements-vercel.txt` - Minimal dependencies without large ML libraries
2. ✅ Updated `vercel.json` - Added `ignore` property and increased `maxLambdaSize` to 250mb
3. ✅ Updated `.vercelignore` - Comprehensive exclusion list

## IMPORTANT: You MUST Use Supabase Mode

Since we're removing `sentence-transformers` from Vercel deployment:

1. **Set `DB_MODE=supabase`** in Vercel environment variables (REQUIRED)
2. **Embeddings will be done via Supabase** - The vector_store_supabase.py uses sentence-transformers, but we need to modify it for Vercel

## Next Steps

### Option 1: Use requirements-vercel.txt (Recommended)

In Vercel Dashboard → Settings → Build & Development Settings:
- Set **Install Command** to: `pip install -r requirements-vercel.txt`

This will use minimal dependencies without large ML models.

### Option 2: Clear Vercel Cache

1. Go to Vercel Dashboard → Your Project → Settings
2. Scroll to "Build & Development Settings"
3. Click "Clear Build Cache"
4. Redeploy

### Option 3: Modify Code to Not Load Models on Vercel

Update `vector_store_supabase.py` to skip model loading if on Vercel:
```python
import os
if os.getenv("VERCEL"):
    # Don't load embedding model on Vercel
    # Use Supabase's built-in embeddings or API
    pass
```

## Why This Happens

The `sentence-transformers` library downloads model files (often 100MB-1GB+) when first imported. On Vercel, this happens during the build/upload phase, causing the 4.3GB error.

## Workaround

Since you're using Supabase, you can:
1. Use Supabase's built-in embedding functions
2. Or call an external embedding API
3. Or pre-compute embeddings and store them

The current setup requires `sentence-transformers` for local mode, but on Vercel with Supabase, you don't need it.
