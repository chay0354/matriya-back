"""
Vercel serverless function wrapper for FastAPI
"""
import sys
import os
from pathlib import Path

# CRITICAL: Set Vercel flag FIRST - before ANY other imports
os.environ["VERCEL"] = "1"

# Setup paths
_back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_back_dir))
os.chdir(str(_back_dir))

# Import app - must be at module level for Vercel
from main import app

# Export handler - Vercel's Python runtime expects this exact name
# Explicitly mark as ASGI app to avoid handler detection issues
handler = app

# Clean up local variables to avoid Vercel handler detection confusion
del _back_dir
del sys, os, Path
