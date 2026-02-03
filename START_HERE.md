# Quick Start - MATRIYA RAG System

## For Python 3.8 Users

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run Python 3.8 compatibility fix** (REQUIRED):
```bash
python fix_all_posthog.py
```

3. **Start the server**:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## For Python 3.9+ Users

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start the server**:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Testing

Once the server is running, you can:

- Visit `http://localhost:8000/docs` for interactive API documentation
- Upload files via the `/ingest/file` endpoint
- Search documents via the `/search` endpoint

See `README.md` for full documentation.
