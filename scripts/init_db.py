#!/usr/bin/env python3
"""
Database initialization script for AttentionSync
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the API directory to Python path
api_path = Path(__file__).parent.parent / "api"
sys.path.insert(0, str(api_path))

from app.core.database import init_db, create_tables
from app.core.config import get_settings
from app.models import User, Source, Item, Collection, UserPreference
import structlog

logger = structlog.get_logger()


async def create_default_user():
    """Create a default admin user for testing"""
    from app.core.database import AsyncSessionLocal
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # Check if admin user already exists
        result = await db.execute(select(User).where(User.email == "admin@attentionsync.io"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info("Default admin user already exists")
            return existing_user
        
        # Create admin user
        admin_user = User(
            email="admin@attentionsync.io",
            username="admin",
            full_name="AttentionSync Admin",
            hashed_password=pwd_context.hash("admin123"),
            is_active=True,
            is_verified=True,
            settings={
                "theme": "light",
                "language": "zh-CN",
                "notifications_enabled": True,
                "daily_digest_time": "07:00"
            }
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        logger.info("Default admin user created", user_id=admin_user.id)
        return admin_user


async def create_sample_sources(user: User):
    """Create sample information sources"""
    from app.core.database import AsyncSessionLocal
    from app.models.source import SourceType, SourceStatus
    
    sample_sources = [
        {
            "name": "Hacker News",
            "description": "Technology and startup news",
            "url": "https://news.ycombinator.com/rss",
            "source_type": SourceType.RSS,
        },
        {
            "name": "36氪",
            "description": "中文科技创业资讯",
            "url": "https://36kr.com/feed",
            "source_type": SourceType.RSS,
        },
        {
            "name": "阮一峰的网络日志",
            "description": "技术博客",
            "url": "http://www.ruanyifeng.com/blog/atom.xml",
            "source_type": SourceType.RSS,
        },
        {
            "name": "少数派",
            "description": "数字生活指南",
            "url": "https://sspai.com/feed",
            "source_type": SourceType.RSS,
        }
    ]
    
    async with AsyncSessionLocal() as db:
        created_sources = []
        
        for source_data in sample_sources:
            source = Source(
                **source_data,
                user_id=user.id,
                status=SourceStatus.ACTIVE,
                fetch_interval_minutes=60,
                config={},
                headers={}
            )
            
            db.add(source)
            created_sources.append(source)
        
        await db.commit()
        
        logger.info("Sample sources created", count=len(created_sources))
        return created_sources


async def create_default_collection(user: User):
    """Create default collection for user"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        default_collection = Collection(
            name="已保存",
            description="默认收藏夹",
            user_id=user.id,
            is_default=True
        )
        
        db.add(default_collection)
        await db.commit()
        
        logger.info("Default collection created", user_id=user.id)
        return default_collection


async def main():
    """Main initialization function"""
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database connections
        await init_db()
        
        # Create all tables
        await create_tables()
        logger.info("Database tables created successfully")
        
        # Create default user
        admin_user = await create_default_user()
        
        # Create sample sources
        await create_sample_sources(admin_user)
        
        # Create default collection
        await create_default_collection(admin_user)
        
        logger.info("Database initialization completed successfully!")
        print("\n✅ Database initialized successfully!")
        print(f"📧 Default admin user: admin@attentionsync.io")
        print(f"🔑 Default password: admin123")
        print(f"🌐 You can now start the API server with: uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())