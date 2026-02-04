"""
Vercel serverless function - Flask WSGI app
Wrapper to avoid Vercel handler detection issues
"""
import os
os.environ["VERCEL"] = "1"

def get_app():
    """Get Flask app instance - delayed import to avoid Vercel detection"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    os.chdir(str(Path(__file__).parent.parent))
    
    try:
        from flask import Flask
        from main import app as flask_app
        return flask_app
    except Exception as e:
        # If import fails, create a minimal error app
        error_app = Flask(__name__)
        @error_app.route("/")
        def error():
            return {"error": f"Import error: {str(e)}"}, 500
        return error_app

# Vercel expects 'handler' to be the WSGI app
handler = get_app()
