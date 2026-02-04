# Vercel Deployment Quick Start

## Quick Deploy

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login**:
   ```bash
   vercel login
   ```

3. **Deploy from the `back` directory**:
   ```bash
   cd back
   vercel
   ```

4. **Set Environment Variables** in Vercel Dashboard:
   - Go to your project → Settings → Environment Variables
   - Add all variables from `env_example.txt`
   - **Important**: Use `POSTGRES_URL` with pooler connection for Vercel

5. **Redeploy**:
   ```bash
   vercel --prod
   ```

## Required Environment Variables

Copy these to Vercel Dashboard:

```
POSTGRES_URL=postgresql://postgres:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=your-supabase-anon-key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-api-key
TOGETHER_MODEL=mistralai/Mistral-7B-Instruct-v0.2
JWT_SECRET=your-random-secret-key
COLLECTION_NAME=documents
```

## Database Setup

Before deploying, make sure your Supabase database has:
1. pgvector extension enabled
2. Tables created (run `supabase_setup_complete.sql` in Supabase SQL Editor)

## Notes

- Files are stored in `/tmp` (ephemeral on Vercel)
- Embeddings use API (Hugging Face or OpenAI) - no local models
- Maximum function timeout: 60 seconds
- Maximum function size: 250MB

See `vercel-deploy.md` for detailed instructions.
