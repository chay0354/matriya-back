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

# Import app in a way that avoids Vercel handler detection issues
# by ensuring the import happens cleanly without exposing problematic variables
try:
    from main import app as fastapi_app
except Exception as e:
    # If import fails, create a minimal error app
    from fastapi import FastAPI
    fastapi_app = FastAPI()
    @fastapi_app.get("/")
    async def error():
        return {"error": f"Import error: {str(e)}"}

# Vercel expects 'handler' - export FastAPI app directly
# Use a different variable name to avoid any potential conflicts
handler = fastapi_app
