# CORS Troubleshooting Guide

## Current Issue

If you're seeing:
```
Access to XMLHttpRequest at 'https://matriya-back.vercel.app/auth/login' from origin 'https://matriya-front.vercel.app' has been blocked by CORS policy
```

## Steps to Fix

### 1. Verify Backend is Deployed with Latest Code

The CORS configuration was updated to include `https://matriya-front.vercel.app`. Make sure:

1. The latest code is pushed to GitHub
2. Vercel has deployed the latest version
3. Check Vercel Dashboard → Deployments → Latest deployment is successful

### 2. Check Backend Logs

1. Go to Vercel Dashboard → Your Backend Project
2. Click on the latest deployment
3. Click "View Function Logs"
4. Look for: `CORS allowed origins: [...]`
5. Verify `https://matriya-front.vercel.app` is in the list

### 3. Test Backend Directly

Test if the backend is responding to OPTIONS requests:

```bash
curl -X OPTIONS https://matriya-back.vercel.app/auth/login \
  -H "Origin: https://matriya-front.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v
```

You should see:
- `Access-Control-Allow-Origin: https://matriya-front.vercel.app`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH`
- `Access-Control-Allow-Headers: *`

### 4. Verify Environment Variables

Make sure no environment variables are overriding CORS settings:
- Check `CORS_ORIGINS` - should include frontend URL or be empty
- Check `ENVIRONMENT` - if set to "production", wildcard won't work

### 5. Force Redeploy

If changes aren't taking effect:
1. Go to Vercel Dashboard → Deployments
2. Click "..." on latest deployment
3. Click "Redeploy"
4. Wait for build to complete

## Current Configuration

The backend is configured to allow:
- ✅ `https://matriya-front.vercel.app` (hardcoded)
- ✅ Origins from `CORS_ORIGINS` environment variable
- ✅ Localhost origins (for development)
- ✅ All origins if `ENVIRONMENT != "production"` (development mode)

## If Still Not Working

1. **Check browser console** - Look for the exact error message
2. **Check Network tab** - See if OPTIONS request is being sent and what response it gets
3. **Check backend logs** - See if requests are reaching the backend
4. **Try setting CORS_ORIGINS** - Set in Vercel Dashboard:
   - Key: `CORS_ORIGINS`
   - Value: `https://matriya-front.vercel.app`
   - Environment: All
