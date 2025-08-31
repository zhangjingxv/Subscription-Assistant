"""
Database - Linus style: One connection, one session, no magic.
"The database is not your friend. It's a necessary evil. Keep it simple."
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Database URL - from env or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attentionsync.db")

# Create engine - once
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # Check connections before using
    echo=False  # Set to True for SQL debugging
)

# Session factory - once
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models - once
Base = declarative_base()


@contextmanager
def get_db() -> Session:
    """Get a database session - simple context manager"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """Initialize database - create tables if needed"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def check_db_health() -> bool:
    """Check if database is accessible"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False