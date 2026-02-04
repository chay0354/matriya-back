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
# Wrap in try/except to provide better error messages
try:
    from main import app
    
    # Vercel expects the app to be exported as 'handler'
    # FastAPI is ASGI-compatible, so it works directly
    handler = app
    
    # Verify handler is callable (ASGI app)
    if not callable(handler):
        raise TypeError("Handler must be callable (ASGI app)")
    
except ImportError as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Failed to import app: {e}", exc_info=True)
    raise
except Exception as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Error setting up handler: {e}", exc_info=True)
    raise

# Export for Vercel
__all__ = ['handler', 'app']
