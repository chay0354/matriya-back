# Complete Vercel Environment Variables

Copy and paste these into **Vercel Dashboard → Settings → Environment Variables**

## Required Variables

### Database Configuration
```
DB_MODE=supabase
```

### Database Connection (CRITICAL - Use Pooler for Vercel)
```
POSTGRES_URL=postgres://postgres.tymorwyygffvruqdtwal:Chaymoalem123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
```

**OR** (if POSTGRES_URL doesn't work, use this as fallback):
```
SUPABASE_DB_URL=postgres://postgres.tymorwyygffvruqdtwal:Chaymoalem123@db.tymorwyygffvruqdtwal.supabase.co:5432/postgres?sslmode=require
```

### Supabase API (Optional - for future use)
```
SUPABASE_URL=https://tymorwyygffvruqdtwal.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5bW9yd3l5Z2ZmdnJ1cWR0d2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxMjM3OTQsImV4cCI6MjA4NTY5OTc5NH0.o7VavWVpWCY7SuN-HnBs2P6_5O4CecxH--e-_rSMpJ0
```

### LLM API Keys (REQUIRED)
```
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-api-key-here
```

**OR** (if using Hugging Face instead):
```
LLM_PROVIDER=huggingface
HF_API_TOKEN=your-huggingface-token-here
```

### JWT Secret Key (Optional but Recommended)
Generate a secure random key:
```
SECRET_KEY=your-random-secret-key-here
```

You can generate one using Python:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Complete List (Copy All)

```
DB_MODE=supabase
POSTGRES_URL=postgres://postgres.tymorwyygffvruqdtwal:Chaymoalem123@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
SUPABASE_URL=https://tymorwyygffvruqdtwal.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5bW9yd3l5Z2ZmdnJ1cWR0d2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxMjM3OTQsImV4cCI6MjA4NTY5OTc5NH0.o7VavWVpWCY7SuN-HnBs2P6_5O4CecxH--e-_rSMpJ0
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-api-key-here
```

## Notes

1. **POSTGRES_URL is CRITICAL** - This uses the pooler connection (port 6543) which supports IPv4 and works on Vercel serverless
2. **TOGETHER_API_KEY** - Replace `your-together-api-key-here` with your actual Together AI API key
3. **SECRET_KEY** - Optional but recommended for production. If not set, a new one is generated on each deployment (users will be logged out)
4. All other settings have defaults and don't need to be set

## How to Set in Vercel

1. Go to **Vercel Dashboard** → Your Project (`matriya-back`)
2. Click **Settings** → **Environment Variables**
3. Click **Add New**
4. For each variable:
   - **Key**: The variable name (e.g., `DB_MODE`)
   - **Value**: The variable value (e.g., `supabase`)
   - **Environment**: Select **Production**, **Preview**, and **Development** (or just Production)
5. Click **Save**
6. **Redeploy** your project for changes to take effect
