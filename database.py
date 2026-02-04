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
import os

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
            error_msg = "SUPABASE_DB_URL must be set when DB_MODE=supabase. Please set it in Vercel environment variables."
            logger.error(error_msg)
            raise ValueError(error_msg)
        return settings.SUPABASE_DB_URL
    else:
        # Local SQLite
        if settings.SQLITE_DB_PATH:
            db_path = Path(settings.SQLITE_DB_PATH)
        else:
            # Auto-generate path next to chroma_db
            db_path = Path(settings.CHROMA_DB_PATH).parent / "users.db"
        # Only try to create directory if not on Vercel
        if not os.getenv("VERCEL"):
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create directory for SQLite DB: {e}")
        return f"sqlite:///{db_path}"


# Create engine based on mode - handle errors gracefully
try:
    DATABASE_URL = get_database_url()
    is_sqlite = DATABASE_URL.startswith("sqlite")
except Exception as e:
    logger.error(f"Failed to get database URL: {e}")
    # On Vercel, we can continue without DB connection for now
    # It will be retried when actually needed
    if os.getenv("VERCEL"):
        DATABASE_URL = None
        is_sqlite = False
        logger.warning("Database URL not available on Vercel startup, will retry on first use")
    else:
        raise


class FilePermission(Base):
    """File permission model - stores which files users can access"""
    __tablename__ = "file_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create engine only if DATABASE_URL is available
if DATABASE_URL:
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
else:
    # On Vercel, create a dummy engine that will be replaced on first use
    engine = None
    logger.warning("Database engine not initialized - will be created on first use")

# Create session factory with optimized settings
# Will be recreated when engine is available
if engine:
    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine,
        expire_on_commit=False  # Faster - don't expire objects on commit
    )
else:
    SessionLocal = None


def init_db():
    """Initialize database tables"""
    if not engine:
        logger.warning("Database engine not available, skipping initialization")
        return
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # On Vercel, don't fail if database connection isn't ready yet
        # Tables will be created on first use
        if os.getenv("VERCEL"):
            logger.warning("Database initialization failed on Vercel, will retry on first use")
        else:
            raise


# Dependency to get DB session
def get_db():
    """Get database session"""
    # Lazy initialization if engine wasn't available at startup
    global engine, SessionLocal, DATABASE_URL, is_sqlite
    if not engine or not SessionLocal:
        try:
            DATABASE_URL = get_database_url()
            is_sqlite = DATABASE_URL.startswith("sqlite")
            if is_sqlite:
                engine = create_engine(
                    DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                if "sslmode" not in DATABASE_URL.lower():
                    separator = "?" if "?" not in DATABASE_URL else "&"
                    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"
                engine = create_engine(
                    DATABASE_URL,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    connect_args={"connect_timeout": 10}
                )
            SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
                expire_on_commit=False
            )
            # Create tables on first use
            Base.metadata.create_all(bind=engine)
            logger.info("Database engine initialized on first use")
        except Exception as e:
            logger.error(f"Failed to initialize database on first use: {e}")
            raise
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
