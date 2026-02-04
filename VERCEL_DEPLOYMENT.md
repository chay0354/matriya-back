# Vercel Deployment Guide for MATRIYA RAG System

## Overview

This guide explains how to deploy the MATRIYA RAG System to Vercel. The system consists of:
- **Frontend**: React application
- **Backend**: FastAPI Python application (deployed as serverless functions)

## Prerequisites

1. Vercel account (sign up at https://vercel.com)
2. Vercel CLI installed: `npm i -g vercel`
3. Supabase account (for production database)
4. Environment variables ready

## Deployment Steps

### Option 1: Deploy Frontend and Backend Separately (Recommended)

#### Step 1: Deploy Backend

1. **Navigate to backend directory:**
   ```bash
   cd back
   ```

2. **Install Vercel CLI if not already installed:**
   ```bash
   npm i -g vercel
   ```

3. **Login to Vercel:**
   ```bash
   vercel login
   ```

4. **Deploy backend:**
   ```bash
   vercel
   ```
   - Follow the prompts
   - **Framework Preset**: Choose "Other" or "Python"
   - **Root Directory**: `./back` (or just `.` if already in back directory)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty

5. **Set Environment Variables:**
   After deployment, go to Vercel Dashboard → Your Project → Settings → Environment Variables
   
   Add these variables:
   ```
   DB_MODE=supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SUPABASE_DB_URL=your_supabase_db_url
   HF_API_TOKEN=your_huggingface_token (optional)
   HF_MODEL=microsoft/phi-2
   LLM_PROVIDER=together
   TOGETHER_API_KEY=your_together_api_key
   TOGETHER_MODEL=togethercomputer/Refuel-Llm-V2-Small
   SECRET_KEY=your_secret_key_for_jwt (generate a random string)
   CORS_ORIGINS=https://your-frontend-domain.vercel.app
   ENVIRONMENT=production
   ```

6. **Note the Backend URL:**
   After deployment, Vercel will give you a URL like: `https://your-backend.vercel.app`
   Copy this URL - you'll need it for the frontend.

#### Step 2: Deploy Frontend

1. **Navigate to frontend directory:**
   ```bash
   cd front
   ```

2. **Create/Update .env file:**
   Create `.env.production`:
   ```
   REACT_APP_API_URL=https://your-backend.vercel.app
   ```

3. **Deploy frontend:**
   ```bash
   vercel
   ```
   - Follow the prompts
   - **Framework Preset**: Choose "Create React App"
   - **Root Directory**: `./front` (or just `.` if already in front directory)
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

4. **Set Environment Variable in Vercel Dashboard:**
   Go to Vercel Dashboard → Your Frontend Project → Settings → Environment Variables
   
   Add:
   ```
   REACT_APP_API_URL=https://your-backend.vercel.app
   ```

5. **Update Backend CORS:**
   Go back to your backend project in Vercel Dashboard → Settings → Environment Variables
   
   Update `CORS_ORIGINS` to include your frontend URL:
   ```
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```

### Option 2: Deploy as Monorepo (Single Project)

1. **Create vercel.json in root:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "front/package.json",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "front/build"
         }
       },
       {
         "src": "back/api/index.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "back/api/index.py"
       },
       {
         "src": "/(.*)",
         "dest": "front/build/index.html"
       }
     ]
   }
   ```

2. **Deploy from root:**
   ```bash
   vercel
   ```

## Framework Presets in Vercel

### For Frontend:
- **Framework**: **Create React App** or **Other**
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install`

### For Backend:
- **Framework**: **Other** or **Python**
- **Build Command**: (Leave empty - Vercel auto-detects)
- **Output Directory**: (Leave empty)
- **Install Command**: (Leave empty - Vercel uses requirements.txt)

## Important Notes

### Backend Considerations:

1. **Serverless Limitations:**
   - Each API call is a separate serverless function
   - Cold starts may occur (first request after inactivity)
   - File uploads are limited (10MB default, can be increased)
   - Long-running operations may timeout (10s default, 60s max for Pro)

2. **Database:**
   - **MUST use Supabase** in production (DB_MODE=supabase)
   - Local SQLite/ChromaDB won't work in serverless environment
   - Vector database must be Supabase pgvector

3. **File Storage:**
   - Uploaded files are stored in `/tmp` (temporary, cleared after function execution)
   - Consider using Supabase Storage or AWS S3 for persistent file storage
   - Or process files immediately and store only in vector DB

4. **Environment Variables:**
   - All sensitive data must be in Vercel Environment Variables
   - Never commit `.env` files
   - Use Vercel Dashboard or CLI to set variables

### Frontend Considerations:

1. **API URL:**
   - Must use environment variable `REACT_APP_API_URL`
   - Set in Vercel Dashboard for production
   - Can use different URLs for different environments

2. **Build Optimization:**
   - Vercel automatically optimizes React builds
   - Static assets are CDN-cached
   - Consider code splitting for large apps

## Troubleshooting

### Backend Issues:

1. **Import Errors:**
   - Make sure all dependencies are in `requirements.txt`
   - Check that `api/index.py` correctly imports from parent directory

2. **Cold Start Timeouts:**
   - First request may be slow (loading models)
   - Consider using Vercel Pro for longer timeouts
   - Or pre-warm functions with scheduled pings

3. **Database Connection:**
   - Ensure Supabase connection string is correct
   - Check SSL mode is enabled
   - Verify network access from Vercel

### Frontend Issues:

1. **API Connection Errors:**
   - Check `REACT_APP_API_URL` is set correctly
   - Verify CORS is configured on backend
   - Check browser console for errors

2. **Build Failures:**
   - Ensure all dependencies are in `package.json`
   - Check for TypeScript/ESLint errors
   - Review build logs in Vercel Dashboard

## Post-Deployment

1. **Test all endpoints:**
   - Login/Signup
   - File upload
   - Search
   - Admin functions

2. **Monitor:**
   - Check Vercel Dashboard for function logs
   - Monitor Supabase for database usage
   - Watch for cold start issues

3. **Optimize:**
   - Enable Vercel Analytics
   - Set up error tracking
   - Configure custom domains

## Custom Domain Setup

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Update `CORS_ORIGINS` in backend to include custom domain

## Support

For issues:
- Check Vercel logs in Dashboard
- Review Supabase logs
- Check browser console for frontend errors
- Review backend function logs in Vercel
