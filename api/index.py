"""
Vercel serverless function wrapper for FastAPI
"""
import sys
import os
from pathlib import Path

# CRITICAL: Set Vercel flag FIRST - before ANY other imports
os.environ["VERCEL"] = "1"

# Setup paths
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))
os.chdir(str(back_dir))

# Import app - must be at module level for Vercel
# The import chain will load everything, but Vercel should detect FastAPI as ASGI
from main import app

# Export handler - Vercel's Python runtime expects this exact name
handler = app
