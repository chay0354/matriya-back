"""
Vercel serverless function - Flask WSGI app
Wrapper to avoid Vercel handler detection issues
"""
import os
os.environ["VERCEL"] = "1"

def _get_flask_app():
    """Get Flask app instance - isolated function to avoid Vercel detection"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    os.chdir(str(Path(__file__).parent.parent))
    
    try:
        from flask import Flask
        import main
        flask_app = main.app
        # Clean up immediately to avoid Vercel scanning
        del main
        return flask_app
    except Exception as e:
        # If import fails, create a minimal error app
        from flask import Flask
        error_app = Flask(__name__)
        @error_app.route("/")
        def error():
            return {"error": f"Import error: {str(e)}"}, 500
        return error_app

# Vercel expects 'handler' to be the WSGI app
# Call the function to get the app, avoiding namespace pollution
handler = _get_flask_app()
# Explicitly control exports to avoid Vercel scanning unwanted variables
__all__ = ['handler']
