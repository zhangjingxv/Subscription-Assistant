"""
Redis connection and utilities
"""

import redis.asyncio as redis
from typing import Optional
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Global Redis connection
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    settings = get_settings()
    
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    if redis_client is None:
        await init_redis()
    
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client
    
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")