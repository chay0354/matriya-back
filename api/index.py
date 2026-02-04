"""
Vercel serverless function wrapper for FastAPI
Vercel Python runtime expects ASGI app
"""
import sys
from pathlib import Path

# Add parent directory to path to import modules
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))

# Change working directory for relative paths
import os
original_cwd = os.getcwd()
os.chdir(str(back_dir))

try:
    from main import app
    
    # Vercel expects the app to be exported
    # FastAPI is ASGI-compatible, so it works directly
    handler = app
except Exception as e:
    # Restore CWD on error
    os.chdir(original_cwd)
    raise
