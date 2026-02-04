"""
Vercel serverless function wrapper for FastAPI
"""
import sys
import os
from pathlib import Path

# Set Vercel environment variable early - MUST be first
os.environ["VERCEL"] = "1"

# Add parent directory to path
back_dir = Path(__file__).parent.parent
sys.path.insert(0, str(back_dir))
os.chdir(str(back_dir))

# Import app - delay any side effects
def get_app():
    """Lazy import to avoid Vercel handler detection issues"""
    from main import app
    return app

# Export handler - explicitly as ASGI app
app = get_app()
handler = app
