"""
Vercel serverless function - FastAPI ASGI app
Minimal wrapper to avoid Vercel handler detection issues
"""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(str(Path(__file__).parent.parent))

from main import app

# Vercel expects 'handler' - export FastAPI app directly
handler = app
