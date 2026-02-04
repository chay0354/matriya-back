# CORS Configuration

## Current Setup

The backend allows CORS requests from:

1. **Localhost origins** (for development):
   - `http://localhost:3000`
   - `http://localhost:8080`
   - `http://127.0.0.1:3000`
   - `http://127.0.0.1:8080`

2. **Vercel Frontend** (production):
   - `https://matriya-front.vercel.app`

3. **Custom origins** (via `CORS_ORIGINS` environment variable):
   - Set `CORS_ORIGINS` in Vercel Dashboard with comma-separated URLs
   - Example: `CORS_ORIGINS=https://example.com,https://another.com`

4. **Development mode**:
   - If `ENVIRONMENT != "production"`, allows all origins (`*`)

## Adding New Origins

### Option 1: Hardcode in `main.py`

Edit `back/main.py` and add to the `allowed_origins` list:
```python
allowed_origins.append("https://your-frontend-url.com")
```

### Option 2: Use Environment Variable (Recommended)

1. Go to Vercel Dashboard → Your Backend Project → Settings → Environment Variables
2. Add:
   - **Key**: `CORS_ORIGINS`
   - **Value**: `https://matriya-front.vercel.app,https://another-url.com`
   - **Environment**: All
3. Redeploy

## Troubleshooting

If you get CORS errors:

1. **Check the origin** - Make sure the frontend URL exactly matches (including `https://` and no trailing slash)
2. **Redeploy backend** - CORS changes require a redeploy
3. **Check browser console** - Look for the exact origin being blocked
4. **Verify environment variable** - If using `CORS_ORIGINS`, make sure it's set correctly

## Current Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This allows:
- ✅ All HTTP methods (GET, POST, PUT, DELETE, etc.)
- ✅ All headers
- ✅ Credentials (cookies, authorization headers)
