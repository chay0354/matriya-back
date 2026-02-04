"""
Flask application for RAG system file ingestion
"""
import logging
import os
from pathlib import Path
from typing import List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import settings
from rag_service import RAGService
from database import init_db, get_db
from auth_endpoints import auth_bp
from admin_endpoints import admin_bp
from state_machine import Kernel, StateMachine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# CORS configuration - Allow all origins
logger.info("CORS configured to allow all origins")
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        "allow_headers": "*",
        "expose_headers": "*",
        "max_age": 3600
    }
})

# Initialize database (non-blocking on Vercel)
# On Vercel, skip initialization at startup to avoid blocking
if not os.getenv("VERCEL"):
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
else:
    # On Vercel, database will be initialized on first use (lazy initialization)
    logger.info("Skipping database initialization on Vercel - will initialize on first use")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Initialize RAG service (lazy initialization to avoid blocking startup)
rag_service = None

def get_rag_service():
    """Get or initialize RAG service"""
    global rag_service
    if rag_service is None:
        logger.info("Initializing RAG service...")
        rag_service = RAGService()
        logger.info("RAG service initialized")
    return rag_service

# Initialize Kernel (lazy initialization)
kernel = None

def get_kernel():
    """Get or initialize Kernel with State Machine"""
    global kernel
    if kernel is None:
        logger.info("Initializing Kernel...")
        # State machine doesn't need DB session for basic operations (logging only)
        state_machine = StateMachine()
        kernel = Kernel(get_rag_service(), state_machine)
        logger.info("Kernel initialized")
    return kernel


@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "MATRIYA RAG System API",
        "version": "1.0.0",
        "status": "running"
    })


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        info = get_rag_service().get_collection_info()
        return jsonify({
            "status": "healthy",
            "vector_db": info
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route("/ingest/file", methods=["POST"])
def ingest_file():
    """
    Upload and ingest a single file
    
    Returns:
        Ingestion result
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"File type {file_ext} not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
        }), 400
    
    # Read file content
    file_content = file.read()
    
    # Validate file size
    if len(file_content) > settings.MAX_FILE_SIZE:
        return jsonify({
            "error": f"File size exceeds maximum of {settings.MAX_FILE_SIZE} bytes"
        }), 400
    
    # Save file temporarily
    # On Vercel, use /tmp directory
    if os.getenv("VERCEL"):
        upload_dir = Path("/tmp")
    else:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file_path = upload_dir / file.filename
    
    try:
        # Write file
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)
        
        # Ingest file
        result = get_rag_service().ingest_file(str(temp_file_path))
        
        # Clean up temp file
        if temp_file_path.exists():
            temp_file_path.unlink()
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "File ingested successfully",
                "data": result
            })
        else:
            return jsonify({
                "error": result.get('error', 'Unknown error during ingestion')
            }), 500
    
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        # Clean up temp file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        return jsonify({
            "error": f"Error ingesting file: {str(e)}"
        }), 500


@app.route("/ingest/directory", methods=["POST"])
def ingest_directory():
    """
    Ingest all supported files from a directory
    
    Returns:
        Ingestion results for all files
    """
    data = request.get_json()
    if not data or 'directory_path' not in data:
        return jsonify({"error": "directory_path is required"}), 400
    
    directory_path = data['directory_path']
    
    if not Path(directory_path).exists():
        return jsonify({
            "error": f"Directory not found: {directory_path}"
        }), 404
    
    try:
        result = get_rag_service().ingest_directory(directory_path)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error ingesting directory: {str(e)}")
        return jsonify({
            "error": f"Error ingesting directory: {str(e)}"
        }), 500


@app.route("/search", methods=["GET"])
def search():
    """
    Search for relevant documents and optionally generate an answer
    
    Query params:
        query: Search query (required)
        n_results: Number of results to return (default: 5)
        filename: Optional filename filter
        generate_answer: Whether to generate AI answer from results (default: true)
        
    Returns:
        Search results and generated answer
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "query parameter is required"}), 400
    
    n_results = request.args.get('n_results', 5, type=int)
    if n_results < 1 or n_results > 50:
        n_results = 5
    
    filename = request.args.get('filename', None)
    generate_answer = request.args.get('generate_answer', 'true').lower() == 'true'
    
    filter_metadata = None
    if filename:
        filter_metadata = {"filename": filename}
    
    try:
        if generate_answer:
            # Process through Kernel (State Machine flow)
            # Flow: User Intent → Kernel → Agents → Kernel → Decision
            kernel = get_kernel()
            kernel_result = kernel.process_user_intent(
                query=query,
                user_id=None,  # Can be added from auth if needed
                context=None,  # Will be generated by Doc Agent
                filter_metadata=filter_metadata  # Pass filename filter to Kernel
            )
            
            # If blocked or stopped, return appropriate response
            if kernel_result['decision'] == 'block' or kernel_result['decision'] == 'stop':
                return jsonify({
                    "query": query,
                    "results_count": 0,
                    "results": [],
                    "answer": None,
                    "context_sources": 0,
                    "context": "",
                    "error": kernel_result.get('reason', 'תשובה נחסמה'),
                    "decision": kernel_result['decision'],
                    "state": kernel_result['state'],
                    "blocked": True,
                    "block_reason": kernel_result.get('reason', '')
                })
            
            # If allowed (with or without warnings)
            return jsonify({
                "query": query,
                "results_count": kernel_result['agent_results']['doc_agent'].get('results_count', 0),
                "results": kernel_result.get('search_results', []),
                "answer": kernel_result['answer'],
                "context_sources": kernel_result['agent_results']['doc_agent'].get('context_sources', 0),
                "context": kernel_result.get('context', ''),  # Include context for agent checks
                "error": None,
                "decision": kernel_result['decision'],
                "state": kernel_result['state'],
                "warning": kernel_result.get('warning'),
                "agent_results": {
                    "contradiction": kernel_result['agent_results']['contradiction_agent'],
                    "risk": kernel_result['agent_results']['risk_agent']
                }
            })
        else:
            # Just return search results
            results = get_rag_service().search(query, n_results, filter_metadata)
            return jsonify({
                "query": query,
                "results_count": len(results),
                "results": results,
                "answer": None
            })
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        return jsonify({
            "error": f"Error searching: {str(e)}"
        }), 500


@app.route("/agent/contradiction", methods=["POST"])
def check_contradiction():
    """
    Contradiction Agent - Checks for contradictions in the answer
    
    JSON body:
        answer: The answer from Doc Agent
        context: The context used to generate the answer
        query: Original user query
        
    Returns:
        Contradiction analysis results
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400
    
    answer = data.get('answer')
    context = data.get('context')
    query = data.get('query')
    
    if not all([answer, context, query]):
        return jsonify({"error": "answer, context, and query are required"}), 400
    
    try:
        result = get_rag_service().check_contradictions(answer, context, query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking contradictions: {str(e)}")
        return jsonify({
            "error": f"Error checking contradictions: {str(e)}"
        }), 500


@app.route("/agent/risk", methods=["POST"])
def check_risk():
    """
    Risk Agent - Identifies risks in the answer
    
    JSON body:
        answer: The answer from Doc Agent
        context: The context used for the answer
        query: Original user query
        
    Returns:
        Risk analysis results
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400
    
    answer = data.get('answer')
    context = data.get('context')
    query = data.get('query')
    
    if not all([answer, context, query]):
        return jsonify({"error": "answer, context, and query are required"}), 400
    
    try:
        result = get_rag_service().check_risks(answer, context, query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking risks: {str(e)}")
        return jsonify({
            "error": f"Error checking risks: {str(e)}"
        }), 500


@app.route("/collection/info", methods=["GET"])
def get_collection_info():
    """Get information about the vector database collection"""
    try:
        info = get_rag_service().get_collection_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        return jsonify({
            "error": f"Error getting collection info: {str(e)}"
        }), 500


@app.route("/files", methods=["GET"])
def get_files():
    """Get list of all uploaded files"""
    try:
        filenames = get_rag_service().get_all_filenames()
        return jsonify({
            "files": filenames,
            "count": len(filenames)
        })
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return jsonify({
            "error": f"Error getting files: {str(e)}"
        }), 500


@app.route("/documents", methods=["DELETE"])
def delete_documents():
    """
    Delete documents by IDs
    
    JSON body:
        ids: List of document IDs to delete
        
    Returns:
        Deletion result
    """
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({"error": "ids array is required"}), 400
    
    ids = data['ids']
    if not isinstance(ids, list):
        return jsonify({"error": "ids must be a list"}), 400
    
    try:
        success = get_rag_service().delete_documents(ids)
        if success:
            return jsonify({
                "success": True,
                "message": f"Deleted {len(ids)} documents",
                "deleted_ids": ids
            })
        else:
            return jsonify({
                "error": "Failed to delete documents"
            }), 500
    except Exception as e:
        logger.error(f"Error deleting documents: {str(e)}")
        return jsonify({
            "error": f"Error deleting documents: {str(e)}"
        }), 500


@app.route("/reset", methods=["POST"])
def reset_database():
    """
    Reset the entire vector database (WARNING: This deletes all data)
    
    Returns:
        Reset result
    """
    try:
        success = get_rag_service().reset_database()
        if success:
            return jsonify({
                "success": True,
                "message": "Database reset successfully"
            })
        else:
            return jsonify({
                "error": "Failed to reset database"
            }), 500
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return jsonify({
            "error": f"Error resetting database: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=True
    )
