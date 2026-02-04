"""
Vercel serverless function wrapper for FastAPI
"""
import sys
import os
from pathlib import Path

# Set Vercel environment variable early
os.environ["VERCEL"] = "1"

# Add parent directory to path
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))
os.chdir(str(back_dir))

# Import and export app
from main import app
handler = app
