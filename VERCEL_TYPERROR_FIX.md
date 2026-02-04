# Vercel TypeError Fix

## The Problem

```
TypeError: issubclass() arg 1 must be a class
File "/var/task/vc__handler__python.py", line 463
```

This error occurs in Vercel's internal handler code, not our code. It happens when Vercel tries to auto-detect the handler type.

## Root Cause

Vercel's Python runtime tries to detect if you're using:
- WSGI app
- ASGI app  
- Standard HTTP server handler

The TypeError suggests Vercel's detection is getting confused, possibly by:
1. Module-level imports that conflict
2. How the handler is exported
3. Vercel runtime version compatibility

## Solutions to Try

### 1. Set POSTGRES_URL (CRITICAL)

**MUST SET THIS IN VERCEL ENVIRONMENT VARIABLES:**

```
POSTGRES_URL=postgres://postgres.tymorwyygffvruqdtwal:Chaymoalem123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
```

This uses the pooler connection (IPv4) which works on Vercel.

### 2. Check Vercel Runtime Version

The `vercel.json` now specifies `runtime: "python3.9"`. If this doesn't work, try:
- Remove the runtime specification (let Vercel auto-detect)
- Or try `python3.10` or `python3.11`

### 3. Simplify Handler Export

The handler is now exported as simply:
```python
from main import app
handler = app
```

This is the standard way for FastAPI on Vercel.

### 4. If Still Failing

The TypeError might be a Vercel runtime bug. Try:
1. Clear Vercel build cache
2. Create a new deployment (not redeploy)
3. Check Vercel status page for known issues
4. Consider using Vercel's newer Python runtime if available

## Current Status

- ✅ Database connection logic fixed (prefers POSTGRES_URL)
- ✅ Handler export simplified
- ✅ Error handling added
- ⚠️ **ACTION REQUIRED**: Set `POSTGRES_URL` in Vercel environment variables

## Next Steps

1. **Set `POSTGRES_URL` in Vercel Dashboard**
2. Redeploy (or wait for auto-deploy)
3. If TypeError persists, it may be a Vercel runtime issue - check Vercel status or try a different Python version
