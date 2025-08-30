"""
Database configuration and connection management
"""

import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Create base class for models
Base = declarative_base()
metadata = MetaData()

# Database engines
engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None


def get_database_url(async_db: bool = False) -> str:
    """Get database URL with appropriate driver"""
    settings = get_settings()
    url = settings.database_url
    
    if async_db:
        # Replace postgresql:// with postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        # Replace postgresql:// with postgresql+psycopg2://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    return url


def init_sync_db():
    """Initialize synchronous database connection"""
    global engine, SessionLocal
    
    database_url = get_database_url(async_db=False)
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=get_settings().debug
    )
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


def init_async_db():
    """Initialize asynchronous database connection"""
    global async_engine, AsyncSessionLocal
    
    database_url = get_database_url(async_db=True)
    
    async_engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=get_settings().debug
    )
    
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


async def init_db():
    """Initialize database connections"""
    try:
        init_sync_db()
        init_async_db()
        logger.info("Database connections initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Get synchronous database session for worker tasks"""
    if SessionLocal is None:
        raise RuntimeError("Sync database not initialized.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """Create all database tables"""
    if async_engine is None:
        raise RuntimeError("Async database engine not initialized.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables (for testing)"""
    if async_engine is None:
        raise RuntimeError("Async database engine not initialized.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("Database tables dropped successfully")