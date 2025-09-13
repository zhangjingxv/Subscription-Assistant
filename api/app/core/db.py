"""
Simple database setup
SQLite for development, PostgreSQL for production
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create engine
if settings.database_url.startswith("sqlite"):
    # SQLite needs special handling for async
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL and others
    engine = create_engine(settings.database_url)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    # Import all models to register them
    from app.models import user, source, item  # noqa
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


async def init_db_async():
    """Async version for FastAPI"""
    init_db()


async def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False