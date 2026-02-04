"""
Vercel serverless function wrapper for FastAPI
Vercel Python runtime expects ASGI app
"""
import sys
import os
from pathlib import Path

# Set Vercel environment variable early - MUST be first
os.environ["VERCEL"] = "1"

# Add parent directory to path to import modules
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))

# Change working directory for relative paths
original_cwd = os.getcwd()
os.chdir(str(back_dir))

# Import app - this must happen at module level for Vercel
from main import app

# Vercel expects the app to be exported as 'handler'
# FastAPI is ASGI-compatible, so it works directly
# Export both 'handler' and 'app' for compatibility
handler = app
__all__ = ['handler', 'app']
