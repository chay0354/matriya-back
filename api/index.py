"""
Vercel serverless function wrapper for FastAPI
Vercel Python runtime - ASGI app export
"""
import sys
import os
from pathlib import Path

# Set Vercel flag FIRST before any other imports
os.environ["VERCEL"] = "1"

# Setup paths
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))
os.chdir(str(back_dir))

# Import FastAPI app
# This must be at module level for Vercel to detect it as ASGI
from main import app

# Export as handler - Vercel expects this name
handler = app

# Explicitly mark as ASGI (not WSGI or HTTP handler)
# This helps Vercel's handler detection
if not hasattr(handler, '__call__'):
    raise TypeError("Handler must be callable (ASGI app)")
