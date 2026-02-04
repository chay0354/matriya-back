"""
Admin endpoints for file management and user permissions
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from database import get_db, User, FilePermission
from auth_endpoints import get_current_user
from rag_service import RAGService
import logging

# Lazy initialization of RAG service
_rag_service = None

def get_rag_service():
    """Get or initialize RAG service (lazy initialization)"""
    global _rag_service
    if _rag_service is None:
        logger.info("Initializing RAG service for admin...")
        _rag_service = RAGService()
        logger.info("RAG service initialized")
    return _rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin(current_user: User = Depends(get_current_user)):
    """Verify that the current user is an admin"""
    # Check both is_admin flag and username
    if not (current_user.is_admin or current_user.username == "admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


@router.get("/files")
async def get_all_files(
    current_user: User = Depends(verify_admin)
):
    """Get all files in the database (admin only)"""
    try:
        rag_service = get_rag_service()
        filenames = rag_service.get_all_filenames()
        return {
            "files": filenames,
            "count": len(filenames)
        }
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting files: {str(e)}"
        )


@router.delete("/files/{filename}")
async def delete_file(
    filename: str,
    current_user: User = Depends(verify_admin)
):
    """Delete a file and all its chunks from the database (admin only)"""
    try:
        rag_service = get_rag_service()
        # Delete documents with matching filename in metadata
        result = rag_service.vector_store.delete_documents(
            filter_metadata={"filename": filename}
        )
        return {
            "success": True,
            "message": f"File '{filename}' deleted successfully",
            "deleted_count": result.get("deleted_count", 0)
        }
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )


@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """Get all users (admin only)"""
    try:
        users = db.query(User).all()
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ],
            "count": len(users)
        }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting users: {str(e)}"
        )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """Get file permissions for a specific user (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has a special "access_all" permission (no specific file permissions = access all)
        permissions = db.query(FilePermission).filter(FilePermission.user_id == user_id).all()
        
        # If no permissions exist, user has access to all files
        access_all_files = len(permissions) == 0
        allowed_files = [p.filename for p in permissions] if not access_all_files else []
        
        return {
            "user_id": user.id,
            "username": user.username,
            "access_all_files": access_all_files,
            "allowed_files": allowed_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting user permissions: {str(e)}"
        )


@router.post("/users/{user_id}/permissions")
async def set_user_permissions(
    user_id: int,
    access_all_files: bool = Body(..., description="Whether user can access all files"),
    allowed_files: List[str] = Body(default=[], description="List of specific files user can access"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """Set file permissions for a specific user (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete existing permissions
        db.query(FilePermission).filter(FilePermission.user_id == user_id).delete()
        
        # If access_all_files is True, don't add any permissions (empty list = access all)
        # If False, add permissions for each allowed file
        if not access_all_files and allowed_files:
            for filename in allowed_files:
                permission = FilePermission(user_id=user_id, filename=filename)
                db.add(permission)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Permissions updated for user {user.username}",
            "user_id": user.id,
            "access_all_files": access_all_files,
            "allowed_files": allowed_files
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting user permissions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error setting user permissions: {str(e)}"
        )
