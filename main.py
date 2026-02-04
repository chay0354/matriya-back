"""
FastAPI application for RAG system file ingestion
"""
import logging
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
from config import settings
from rag_service import RAGService
from database import init_db, get_db
from auth_endpoints import router as auth_router
from admin_endpoints import router as admin_router
from state_machine import Kernel, StateMachine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MATRIYA RAG System",
    description="RAG system for document ingestion and vector storage with user authentication",
    version="1.0.0"
)

# Initialize database
init_db()

# Include authentication router
app.include_router(auth_router)
# Include admin router
app.include_router(admin_router)

# CORS middleware - Allow frontend access
# Get allowed origins from environment or use defaults
allowed_origins = []

# Add origins from CORS_ORIGINS environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allowed_origins.extend([origin.strip() for origin in cors_origins_env.split(",") if origin.strip()])

# Add default localhost origins
allowed_origins.extend([
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "file://",  # Allow file:// protocol for direct HTML opening
])

# Add Vercel frontend URL (production)
allowed_origins.append("https://matriya-front.vercel.app")

# Add Vercel deployment URL if available (backend's own URL - for reference)
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")

# In development, allow all origins
if os.getenv("ENVIRONMENT") != "production":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MATRIYA RAG System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        info = get_rag_service().get_collection_info()
        return {
            "status": "healthy",
            "vector_db": info
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """
    Upload and ingest a single file
    
    Args:
        file: File to upload
        
    Returns:
        Ingestion result
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Save file temporarily
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file_path = upload_dir / file.filename
    
    try:
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(file_content)
        
        # Ingest file
        result = get_rag_service().ingest_file(str(temp_file_path))
        
        # Clean up temp file
        if temp_file_path.exists():
            temp_file_path.unlink()
        
        if result['success']:
            return {
                "success": True,
                "message": "File ingested successfully",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error during ingestion')
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        # Clean up temp file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting file: {str(e)}"
        )


@app.post("/ingest/directory")
async def ingest_directory(directory_path: str):
    """
    Ingest all supported files from a directory
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Ingestion results for all files
    """
    if not Path(directory_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {directory_path}"
        )
    
    try:
        result = get_rag_service().ingest_directory(directory_path)
        return result
    except Exception as e:
        logger.error(f"Error ingesting directory: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting directory: {str(e)}"
        )


@app.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(5, ge=1, le=50, description="Number of results"),
    filename: Optional[str] = Query(None, description="Filter by filename"),
    generate_answer: bool = Query(True, description="Generate AI answer")
):
    """
    Search for relevant documents and optionally generate an answer
    
    Args:
        query: Search query
        n_results: Number of results to return
        filename: Optional filename filter
        generate_answer: Whether to generate AI answer from results
        
    Returns:
        Search results and generated answer
    """
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
                return {
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
                }
            
            # If allowed (with or without warnings)
            return {
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
            }
        else:
            # Just return search results
            results = get_rag_service().search(query, n_results, filter_metadata)
            return {
                "query": query,
                "results_count": len(results),
                "results": results,
                "answer": None
            }
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching: {str(e)}"
        )


@app.post("/agent/contradiction")
async def check_contradiction(
    answer: str = Body(..., description="The answer to check"),
    context: str = Body(..., description="The context used for the answer"),
    query: str = Body(..., description="Original user query")
):
    """
    Contradiction Agent - Checks for contradictions in the answer
    
    Args:
        answer: The answer from Doc Agent
        context: The context used to generate the answer
        query: Original user query
        
    Returns:
        Contradiction analysis results
    """
    try:
        result = get_rag_service().check_contradictions(answer, context, query)
        return result
    except Exception as e:
        logger.error(f"Error checking contradictions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking contradictions: {str(e)}"
        )


@app.post("/agent/risk")
async def check_risk(
    answer: str = Body(..., description="The answer to check"),
    context: str = Body(..., description="The context used for the answer"),
    query: str = Body(..., description="Original user query")
):
    """
    Risk Agent - Identifies risks in the answer
    
    Args:
        answer: The answer from Doc Agent
        context: The context used to generate the answer
        query: Original user query
        
    Returns:
        Risk analysis results
    """
    try:
        result = get_rag_service().check_risks(answer, context, query)
        return result
    except Exception as e:
        logger.error(f"Error checking risks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking risks: {str(e)}"
        )


@app.get("/collection/info")
async def get_collection_info():
    """Get information about the vector database collection"""
    try:
        info = get_rag_service().get_collection_info()
        return info
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting collection info: {str(e)}"
        )


@app.get("/files")
async def get_files():
    """Get list of all uploaded files"""
    try:
        filenames = get_rag_service().get_all_filenames()
        return {
            "files": filenames,
            "count": len(filenames)
        }
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting files: {str(e)}"
        )


@app.delete("/documents")
async def delete_documents(ids: List[str]):
    """
    Delete documents by IDs
    
    Args:
        ids: List of document IDs to delete
        
    Returns:
        Deletion result
    """
    try:
        success = get_rag_service().delete_documents(ids)
        if success:
            return {
                "success": True,
                "message": f"Deleted {len(ids)} documents",
                "deleted_ids": ids
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete documents"
            )
    except Exception as e:
        logger.error(f"Error deleting documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting documents: {str(e)}"
        )


@app.post("/reset")
async def reset_database():
    """
    Reset the entire vector database (WARNING: This deletes all data)
    
    Returns:
        Reset result
    """
    try:
        success = get_rag_service().reset_database()
        if success:
            return {
                "success": True,
                "message": "Database reset successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset database"
            )
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting database: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
