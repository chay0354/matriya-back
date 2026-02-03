# Quick Start Guide

## Installation Steps

1. **Navigate to the backend directory**:
```bash
cd back
```

2. **Create and activate virtual environment**:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

**Note**: The first time you run the system, it will download the embedding model (~80MB). This happens automatically.

## Running the System

### Option 1: Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Option 2: Use the Test Script

For quick testing without the API:

```bash
# Ingest a file
python test_ingestion.py ingest path/to/your/document.pdf

# Search
python test_ingestion.py search "your query here"

# Get collection info
python test_ingestion.py info
```

## Testing with API

### Using curl

1. **Upload a file**:
```bash
curl -X POST "http://localhost:8000/ingest/file" -F "file=@document.pdf"
```

2. **Search**:
```bash
curl "http://localhost:8000/search?query=financial%20report&n_results=5"
```

3. **Check health**:
```bash
curl "http://localhost:8000/health"
```

### Using Python requests

```python
import requests

# Upload file
with open('document.pdf', 'rb') as f:
    response = requests.post('http://localhost:8000/ingest/file', files={'file': f})
    print(response.json())

# Search
response = requests.get('http://localhost:8000/search', params={'query': 'financial report'})
print(response.json())
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Directory Structure

After running, you'll see:
- `chroma_db/` - Vector database (created automatically)
- `uploads/` - Temporary upload directory (created automatically)

## Supported File Formats

- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)
- Excel Files (`.xlsx`, `.xls`)

## Troubleshooting

### Port already in use
Change the port in `config.py` or set `API_PORT` environment variable.

### Out of memory
Reduce `CHUNK_SIZE` in `config.py` or process fewer files at once.

### Model download issues
The model downloads automatically. If it fails, check your internet connection. The model is cached after first download.
