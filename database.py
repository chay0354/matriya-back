"""
Database setup for user management - supports both local SQLite and Supabase PostgreSQL
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path
from config import settings
import logging

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    # Use SERIAL for PostgreSQL, INTEGER for SQLite
    # SQLAlchemy will auto-detect based on database
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


# Database connection setup
def get_database_url():
    """Get database URL based on DB_MODE"""
    if settings.DB_MODE.lower() == "supabase":
        if not settings.SUPABASE_DB_URL:
            raise ValueError("SUPABASE_DB_URL must be set when DB_MODE=supabase")
        return settings.SUPABASE_DB_URL
    else:
        # Local SQLite
        if settings.SQLITE_DB_PATH:
            db_path = Path(settings.SQLITE_DB_PATH)
        else:
            # Auto-generate path next to chroma_db
            db_path = Path(settings.CHROMA_DB_PATH).parent / "users.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"


# Create engine based on mode
DATABASE_URL = get_database_url()
is_sqlite = DATABASE_URL.startswith("sqlite")


class FilePermission(Base):
    """File permission model - stores which files users can access"""
    __tablename__ = "file_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False
    )
    logger.info(f"Using local SQLite database: {DATABASE_URL}")
else:
    # Parse connection string to add SSL mode if not present
    if "sslmode" not in DATABASE_URL.lower():
        # Add sslmode if connection string doesn't have it
        separator = "?" if "?" not in DATABASE_URL else "&"
        DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"
    
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,  # Wait up to 30 seconds for a connection from pool
        connect_args={
            "connect_timeout": 10,  # 10 second connection timeout
        }
    )
    logger.info(f"Using Supabase PostgreSQL database")

# Create session factory with optimized settings
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Faster - don't expire objects on commit
)


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# Dependency to get DB session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
