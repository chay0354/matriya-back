# Vercel Deployment Guide

## Prerequisites

1. Vercel account
2. Supabase project with PostgreSQL database
3. Required API keys

## Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

### Required Variables

```env
# Database (Supabase PostgreSQL)
POSTGRES_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres?pgbouncer=true
# OR
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Supabase (optional, for Supabase client)
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM Provider (Together AI or Hugging Face)
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-api-key
TOGETHER_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# OR Hugging Face
HF_API_TOKEN=your-hf-token
HF_MODEL=microsoft/phi-2

# Optional: OpenAI for better embeddings
OPENAI_API_KEY=your-openai-key

# JWT Secret (auto-generated if not set, but recommended to set)
JWT_SECRET=your-random-secret-key

# Collection Name
COLLECTION_NAME=documents
```

### Optional Variables

```env
# API Settings (defaults work fine)
API_HOST=0.0.0.0
API_PORT=8000

# File Upload Settings
MAX_FILE_SIZE=52428800
UPLOAD_DIR=/tmp
```

## Deployment Steps

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Navigate to backend directory**:
   ```bash
   cd back
   ```

4. **Deploy**:
   ```bash
   vercel
   ```
   
   Or for production:
   ```bash
   vercel --prod
   ```

5. **Set Environment Variables**:
   - Go to Vercel Dashboard
   - Select your project
   - Go to Settings → Environment Variables
   - Add all required variables from above

6. **Redeploy** after setting environment variables:
   ```bash
   vercel --prod
   ```

## Important Notes

- **File Uploads**: On Vercel, files are stored in `/tmp` (ephemeral storage)
- **Embeddings**: Uses API-based embeddings (Hugging Face or OpenAI) since local models aren't available on serverless
- **Database**: Must use Supabase PostgreSQL with pgvector extension
- **Cold Starts**: First request may be slower due to serverless cold starts
- **Timeout**: Maximum function duration is 60 seconds (configured in vercel.json)

## Database Setup

Make sure your Supabase database has:
1. pgvector extension enabled
2. Documents table created (see `supabase_setup_complete.sql`)
3. Users and file_permissions tables created

Run the SQL from `supabase_setup_complete.sql` in your Supabase SQL Editor.

## Testing Deployment

After deployment, test the API:

```bash
# Health check
curl https://your-project.vercel.app/health

# Root endpoint
curl https://your-project.vercel.app/
```

## Troubleshooting

- **502 Errors**: Check function logs in Vercel dashboard
- **Database Connection Issues**: Verify POSTGRES_URL is correct and uses pooler connection
- **Timeout Errors**: Large file uploads may timeout - consider chunking or increasing timeout
- **Memory Issues**: Check function memory usage in Vercel dashboard
