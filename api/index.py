"""
Vercel serverless function - Flask WSGI app
"""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(str(Path(__file__).parent.parent))

# Import Flask app
try:
    from main import app
    # Vercel expects 'handler' to be the WSGI app
    handler = app
except Exception as e:
    # If import fails, create a minimal error app
    from flask import Flask
    handler = Flask(__name__)
    @handler.route("/")
    def error():
        return {"error": f"Import error: {str(e)}"}, 500
