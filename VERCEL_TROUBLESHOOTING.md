# Vercel Deployment Troubleshooting

## If you still get "ERR_OUT_OF_RANGE" error:

### Option 1: Check what Vercel is trying to upload
1. Go to Vercel Dashboard → Your Project → Deployments
2. Click on the failed deployment
3. Check the build logs to see which files are being uploaded
4. Look for files larger than 50MB

### Option 2: Use Vercel CLI with explicit ignore
```bash
cd back
vercel --force
```

### Option 3: Clean git history (if large files were committed before)
```bash
# Remove large files from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch -r chroma_db/ uploads/ users.db" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history)
git push origin --force --all
```

### Option 4: Create a minimal deployment package
Create a `deploy/` directory with only necessary files:
```bash
mkdir deploy
cp -r api/ deploy/
cp *.py deploy/  # Only Python files, not data
cp requirements.txt deploy/
cp vercel.json deploy/
# Then deploy from deploy/ directory
```

### Option 5: Use Vercel's file size limits
Update `vercel.json`:
```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 60,
      "memory": 3008
    }
  },
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb",
        "includeFiles": "api/**"
      }
    }
  ]
}
```

## Most Common Issue

The problem is usually that **ChromaDB database files are in the repository**. Since you're using Supabase in production, you don't need them:

1. ✅ Make sure `DB_MODE=supabase` in Vercel environment variables
2. ✅ Ensure `chroma_db/` is in `.gitignore` and `.vercelignore`
3. ✅ Remove any large files from git: `git rm --cached <file>`
4. ✅ Redeploy

## Verify Before Deploying

Check repository size:
```bash
git count-objects -vH
```

If it's very large (>100MB), there are likely large files in the history.
