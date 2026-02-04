# Quick Vercel Deployment Guide

## Framework Presets to Choose in Vercel

### For Frontend (React App):
1. **Framework Preset**: **Create React App**
2. **Root Directory**: `front` (or leave empty if deploying from front directory)
3. **Build Command**: `npm run build` (auto-detected)
4. **Output Directory**: `build` (auto-detected)
5. **Install Command**: `npm install` (auto-detected)

### For Backend (FastAPI):
1. **Framework Preset**: **Other** or **Python**
2. **Root Directory**: `back` (or leave empty if deploying from back directory)
3. **Build Command**: (Leave empty - Vercel auto-detects)
4. **Output Directory**: (Leave empty)
5. **Install Command**: (Leave empty - Vercel uses requirements.txt)

## Quick Deployment Steps

### 1. Deploy Backend First

```bash
cd back
vercel
```

**When prompted:**
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No**
- Project name? **matriya-backend** (or your choice)
- Directory? **./back** or **.**
- Override settings? **No**

**After deployment:**
- Note the URL: `https://your-backend.vercel.app`
- Go to Vercel Dashboard → Settings → Environment Variables
- Add all environment variables (see VERCEL_DEPLOYMENT.md)

### 2. Deploy Frontend

```bash
cd front
vercel
```

**When prompted:**
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No**
- Project name? **matriya-frontend** (or your choice)
- Directory? **./front** or **.**
- Override settings? **No**

**After deployment:**
- Go to Vercel Dashboard → Settings → Environment Variables
- Add: `REACT_APP_API_URL=https://your-backend.vercel.app`
- Update backend CORS_ORIGINS to include frontend URL

## Required Environment Variables

### Backend:
```
DB_MODE=supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_URL=your_supabase_db_url
TOGETHER_API_KEY=your_together_api_key
TOGETHER_MODEL=togethercomputer/Refuel-Llm-V2-Small
SECRET_KEY=your_random_secret_key
CORS_ORIGINS=https://your-frontend.vercel.app
ENVIRONMENT=production
```

### Frontend:
```
REACT_APP_API_URL=https://your-backend.vercel.app
```

## Important Notes

⚠️ **You MUST use Supabase in production** - Local SQLite/ChromaDB won't work on Vercel serverless functions.

⚠️ **Set CORS_ORIGINS** in backend to your frontend URL to allow API calls.

⚠️ **File uploads** are limited to 10MB on Vercel free tier (can be increased on Pro).

## Testing After Deployment

1. Visit your frontend URL
2. Try to sign up/login
3. Upload a test file
4. Search for content
5. Check Vercel function logs if issues occur

## Need Help?

See `VERCEL_DEPLOYMENT.md` for detailed instructions and troubleshooting.
