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

# Import app directly but ensure clean namespace
# Vercel expects 'handler' to be the ASGI app
try:
    # Import in a way that minimizes namespace pollution
    import main
    handler = main.app
    # Clean up the import reference to avoid Vercel scanning
    del main
except Exception as e:
    # If import fails, create a minimal error app
    from fastapi import FastAPI
    handler = FastAPI()
    @handler.get("/")
    async def error():
        return {"error": f"Import error: {str(e)}"}
