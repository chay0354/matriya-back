"""
Admin endpoints for file management and user permissions
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from functools import wraps
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

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def verify_admin(f):
    """Decorator to verify that the current user is an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check both is_admin flag and username
        if not (user.is_admin or user.username == "admin"):
            return jsonify({"error": "Admin access required"}), 403
        
        # Pass user to the route function
        return f(user, *args, **kwargs)
    return decorated_function


@admin_bp.route("/files", methods=["GET"])
@verify_admin
def get_all_files(user):
    """Get all files in the database (admin only)"""
    try:
        rag_service = get_rag_service()
        filenames = rag_service.get_all_filenames()
        return jsonify({
            "files": filenames,
            "count": len(filenames)
        })
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({
            "error": f"Error getting files: {str(e)}"
        }), 500


@admin_bp.route("/files/<filename>", methods=["DELETE"])
@verify_admin
def delete_file(user, filename):
    """Delete a file and all its chunks from the database (admin only)"""
    try:
        rag_service = get_rag_service()
        # Delete documents with matching filename in metadata
        result = rag_service.vector_store.delete_documents(
            filter_metadata={"filename": filename}
        )
        return jsonify({
            "success": True,
            "message": f"File '{filename}' deleted successfully",
            "deleted_count": result.get("deleted_count", 0)
        })
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({
            "error": f"Error deleting file: {str(e)}"
        }), 500


@admin_bp.route("/users", methods=["GET"])
@verify_admin
def get_all_users(user):
    """Get all users (admin only)"""
    db = next(get_db())
    try:
        users = db.query(User).all()
        return jsonify({
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
        })
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({
            "error": f"Error getting users: {str(e)}"
        }), 500
    finally:
        db.close()


@admin_bp.route("/users/<int:user_id>/permissions", methods=["GET"])
@verify_admin
def get_user_permissions(user, user_id):
    """Get file permissions for a specific user (admin only)"""
    db = next(get_db())
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has a special "access_all" permission (no specific file permissions = access all)
        permissions = db.query(FilePermission).filter(FilePermission.user_id == user_id).all()
        
        # If no permissions exist, user has access to all files
        access_all_files = len(permissions) == 0
        allowed_files = [p.filename for p in permissions] if not access_all_files else []
        
        return jsonify({
            "user_id": target_user.id,
            "username": target_user.username,
            "access_all_files": access_all_files,
            "allowed_files": allowed_files
        })
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return jsonify({
            "error": f"Error getting user permissions: {str(e)}"
        }), 500
    finally:
        db.close()


@admin_bp.route("/users/<int:user_id>/permissions", methods=["POST"])
@verify_admin
def set_user_permissions(user, user_id):
    """Set file permissions for a specific user (admin only)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400
    
    access_all_files = data.get('access_all_files')
    allowed_files = data.get('allowed_files', [])
    
    if access_all_files is None:
        return jsonify({"error": "access_all_files is required"}), 400
    
    if not isinstance(allowed_files, list):
        return jsonify({"error": "allowed_files must be a list"}), 400
    
    db = next(get_db())
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return jsonify({"error": "User not found"}), 404
        
        # Delete existing permissions
        db.query(FilePermission).filter(FilePermission.user_id == user_id).delete()
        
        # If access_all_files is True, don't add any permissions (empty list = access all)
        # If False, add permissions for each allowed file
        if not access_all_files and allowed_files:
            for filename in allowed_files:
                permission = FilePermission(user_id=user_id, filename=filename)
                db.add(permission)
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": f"Permissions updated for user {target_user.username}",
            "user_id": target_user.id,
            "access_all_files": access_all_files,
            "allowed_files": allowed_files
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting user permissions: {e}")
        return jsonify({
            "error": f"Error setting user permissions: {str(e)}"
        }), 500
    finally:
        db.close()
