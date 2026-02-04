# MATRIYA RAG System - Node.js Backend

This is the Node.js version of the MATRIYA RAG System backend. It has been converted from Python to Node.js and maintains the same functionality and API endpoints.

## Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (create a `.env` file):
```env
# Database Mode: "local" or "supabase"
DB_MODE=supabase

# Supabase Settings
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_URL=your_postgres_connection_string
# Or use:
POSTGRES_URL=your_postgres_pooler_url

# LLM Configuration
LLM_PROVIDER=together  # or "huggingface"
TOGETHER_API_KEY=your_together_api_key
TOGETHER_MODEL=mistralai/Mistral-7B-Instruct-v0.2
HF_API_TOKEN=your_hf_token
HF_MODEL=microsoft/phi-2

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# JWT Secret (auto-generated if not set)
JWT_SECRET=your_jwt_secret

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

## Running the Server

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

## API Endpoints

All endpoints are the same as the Python version:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /ingest/file` - Upload and ingest a file
- `POST /ingest/directory` - Ingest all files from a directory
- `GET /search` - Search for documents
- `POST /agent/contradiction` - Check for contradictions
- `POST /agent/risk` - Check for risks
- `GET /collection/info` - Get collection info
- `GET /files` - Get all files
- `DELETE /documents` - Delete documents
- `POST /reset` - Reset database

### Authentication Endpoints
- `POST /auth/signup` - Create user account
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user info

### Admin Endpoints
- `GET /admin/files` - Get all files (admin only)
- `DELETE /admin/files/:filename` - Delete file (admin only)
- `GET /admin/users` - Get all users (admin only)
- `GET /admin/users/:user_id/permissions` - Get user permissions (admin only)
- `POST /admin/users/:user_id/permissions` - Set user permissions (admin only)

## Differences from Python Version

1. **Database**: Uses Sequelize ORM instead of SQLAlchemy
2. **File Uploads**: Uses Multer instead of Flask's request.files
3. **Vector Store**: Currently only supports Supabase (pgvector). Local ChromaDB mode not implemented.
4. **Embeddings**: Uses Hugging Face Inference API for embeddings (no local sentence-transformers)

## Vercel Deployment

The backend is configured for Vercel deployment. The `api/index.js` file serves as the serverless function entry point.

Make sure to set all required environment variables in Vercel's dashboard.

## Notes

- The Node.js version maintains 100% API compatibility with the Python version
- All endpoints return the same JSON responses
- Authentication and authorization work the same way
- The state machine and kernel logic are identical
