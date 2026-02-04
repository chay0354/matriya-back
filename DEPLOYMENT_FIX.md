# Vercel Deployment Fix for Large Files

## Problem
Vercel was trying to upload 4.3GB+ files (ChromaDB database), causing deployment to fail.

## Solution Applied

1. **Updated `.vercelignore`** - Excludes all large files and data directories
2. **Updated `.gitignore`** - Ensures large files aren't tracked in git
3. **Removed `users.db` from git** - Was accidentally committed
4. **Updated `vercel.json`** - Added maxLambdaSize configuration

## Important Notes

⚠️ **You MUST use Supabase in production** - The local ChromaDB and SQLite databases are NOT needed on Vercel.

⚠️ **Environment Variables Required:**
- `DB_MODE=supabase` (MUST be set to supabase)
- All Supabase credentials
- All API keys

## If Deployment Still Fails

1. **Check Vercel Build Logs** - Look for which files are being uploaded
2. **Verify `.vercelignore` is working** - Check that large files are excluded
3. **Check Git Repository Size:**
   ```bash
   git count-objects -vH
   ```
4. **Remove large files from git history** (if needed):
   ```bash
   git filter-branch --tree-filter 'rm -rf chroma_db/ uploads/ users.db' HEAD
   ```

## Alternative: Use Vercel CLI with --force

If files are still being included, try:
```bash
vercel --force
```

This will rebuild from scratch.
