"""
Authentication endpoints for MATRIYA RAG System
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
from functools import wraps
import logging
from database import get_db
from auth import (
    authenticate_user, create_user, verify_token,
    get_user_by_username, get_user_by_email,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def get_current_user():
    """Get current authenticated user from token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return None
    except ValueError:
        return None
    
    payload = verify_token(token)
    if payload is None:
        return None
    
    username: str = payload.get("sub")
    if username is None:
        return None
    
    # Get database session
    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == username).first()
        return user
    finally:
        db.close()


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({
                "error": "Invalid authentication credentials"
            }), 401
        # Pass user to the route function
        return f(user, *args, **kwargs)
    return decorated_function


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new user account
    
    JSON body:
        username: Username
        email: Email address
        password: Password
        full_name: Optional full name
        
    Returns:
        Access token and user information
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    if not all([username, email, password]):
        return jsonify({"error": "username, email, and password are required"}), 400
    
    # Basic email validation
    if '@' not in email:
        return jsonify({"error": "Invalid email format"}), 400
    
    db = next(get_db())
    try:
        # Check if username already exists
        if get_user_by_username(db, username):
            return jsonify({
                "error": "Username already registered"
            }), 400
        
        # Check if email already exists
        if get_user_by_email(db, email):
            return jsonify({
                "error": "Email already registered"
            }), 400
        
        # Create user
        user = create_user(
            db=db,
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin
            }
        })
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login and get access token
    
    JSON body:
        username: Username
        password: Password
        
    Returns:
        Access token and user information
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({"error": "username and password are required"}), 400
    
    db = next(get_db())
    try:
        user = authenticate_user(db, username, password)
        if not user:
            return jsonify({
                "error": "Incorrect username or password"
            }), 401
        
        # Update last login
        from datetime import datetime
        try:
            user.last_login = datetime.utcnow()
            db.commit()
        except:
            db.rollback()
            # Don't fail login if last_login update fails
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin
            }
        })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "error": f"Login failed: {str(e)}"
        }), 500
    finally:
        db.close()


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user_info(user):
    """
    Get current user information
    
    Returns:
        Current user information
    """
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })
