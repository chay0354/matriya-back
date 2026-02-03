# MATRIYA RAG System - Backend

This is the RAG (Retrieval-Augmented Generation) backend service for the MATRIYA system. It provides document ingestion, vector storage, and search capabilities using local technologies.

## Features

- **Local Vector Database**: Uses ChromaDB for persistent, local vector storage
- **Local Embeddings**: Uses sentence-transformers for local embedding generation (no API calls)
- **Multiple File Formats**: Supports PDF, DOCX, TXT, DOC, XLSX, XLS
- **Intelligent Chunking**: Splits documents into semantic chunks with overlap
- **RESTful API**: FastAPI-based API for file upload and search
- **Fully Local**: No external API dependencies for core functionality

## Installation

1. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Python 3.8 Compatibility Fix** (REQUIRED if using Python 3.8):
```bash
python fix_all_posthog.py
```
This fixes compatibility issues with ChromaDB's posthog dependency. Only needs to be run once after installation.

4. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Start the API Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Upload and Ingest a File
```bash
POST /ingest/file
Content-Type: multipart/form-data
Body: file (binary)
```

Example using curl:
```bash
curl -X POST "http://localhost:8000/ingest/file" \
  -F "file=@document.pdf"
```

#### Ingest Directory
```bash
POST /ingest/directory
Body: {"directory_path": "/path/to/directory"}
```

#### Search Documents
```bash
GET /search?query=your search query&n_results=5
```

Example:
```bash
curl "http://localhost:8000/search?query=financial%20report&n_results=5"
```

#### Get Collection Info
```bash
GET /collection/info
```

#### Delete Documents
```bash
DELETE /documents
Body: {"ids": ["id1", "id2", ...]}
```

#### Reset Database
```bash
POST /reset
```

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

### Components

1. **DocumentProcessor**: Extracts text from various file formats
2. **TextChunker**: Splits documents into chunks for embedding
3. **VectorStore**: Manages ChromaDB operations and embeddings
4. **RAGService**: Orchestrates the entire pipeline

### Data Flow

```
File Upload → Document Processing → Text Extraction → Chunking → 
Embedding Generation → Vector Storage (ChromaDB)
```

### Vector Database

- **Location**: `./chroma_db` (configurable)
- **Collection**: `documents` (configurable)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (local, configurable)

## Configuration

All settings can be configured via environment variables or `.env` file:

- `CHROMA_DB_PATH`: Path to ChromaDB database
- `COLLECTION_NAME`: Name of the collection
- `EMBEDDING_MODEL`: Embedding model name
- `UPLOAD_DIR`: Temporary upload directory
- `MAX_FILE_SIZE`: Maximum file size in bytes
- `CHUNK_SIZE`: Size of text chunks
- `CHUNK_OVERLAP`: Overlap between chunks
- `API_HOST`: API host address
- `API_PORT`: API port number

## Development

### Project Structure

```
back/
├── main.py                 # FastAPI application
├── rag_service.py          # Main RAG service
├── document_processor.py   # Document processing
├── chunker.py              # Text chunking
├── vector_store.py         # Vector database management
├── config.py               # Configuration
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Notes

- The embedding model will be downloaded automatically on first use
- ChromaDB creates a persistent database in the specified path
- All processing is done locally - no external API calls required
- The system is designed to handle large volumes of documents

## Next Steps

This is the foundation for the MATRIYA system. Future enhancements will include:
- Kernel-based decision making
- Agent system (Doc Agent, Contradiction Agent, Risk Agent)
- State machine for information governance
- User management and permissions
- Audit logging
- Integration with MOP system
