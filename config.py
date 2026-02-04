"""
Configuration settings for the RAG system
"""
import os
# Disable ChromaDB telemetry before any imports to avoid Python 3.8 compatibility issues
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

from pathlib import Path
# Import BaseSettings with alias to avoid Vercel handler detection issues
from pydantic_settings import BaseSettings as _PydanticBaseSettings
from typing import Optional

class Settings(_PydanticBaseSettings):
    # Vector Database Settings
    CHROMA_DB_PATH: str = "./chroma_db"
    COLLECTION_NAME: str = "documents"
    
    # Embedding Model (local)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Document Processing
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".txt", ".doc", ".xlsx", ".xls"]
    
    # Chunking Settings
    CHUNK_SIZE: int = 500  # Reduced for better chunking
    CHUNK_OVERLAP: int = 100  # Reduced overlap
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database Mode: "local" or "supabase"
    DB_MODE: str = "local"
    
    # Local Database Settings (when DB_MODE=local)
    CHROMA_DB_PATH: str = "./chroma_db"
    SQLITE_DB_PATH: Optional[str] = None  # Auto-generated if None
    
    # Supabase Settings (when DB_MODE=supabase)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None  # PostgreSQL connection string
    
    # LLM API Configuration (Together AI or Hugging Face)
    LLM_PROVIDER: str = "together"  # "together" or "huggingface"
    TOGETHER_API_KEY: Optional[str] = None
    TOGETHER_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    HF_API_TOKEN: Optional[str] = None
    HF_MODEL: str = "microsoft/phi-2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create directories if they don't exist
settings = Settings()
# Only create local directories if in local mode and not on Vercel
if settings.DB_MODE.lower() == "local" and not os.getenv("VERCEL"):
    try:
        Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # On Vercel, we don't need local directories
        pass

# Only create uploads directory if not on Vercel (Vercel uses /tmp)
if not os.getenv("VERCEL"):
    try:
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # On Vercel, we'll use /tmp for uploads
        pass
