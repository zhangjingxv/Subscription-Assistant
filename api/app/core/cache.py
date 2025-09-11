"""
高性能缓存策略实现
支持多层缓存和智能失效策略
"""

import json
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """统一缓存管理器"""
    
    def __init__(self):
        self.redis_client = None
        self._local_cache: Dict[str, Dict] = {}
        self._local_cache_max_size = 1000
        
    async def init_redis(self):
        """初始化 Redis 连接"""
        if not settings.redis_url:
            logger.warning("Redis URL not configured, using local cache only")
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=100,
                retry_on_timeout=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return f"attentionsync:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 先检查本地缓存
        if key in self._local_cache:
            cache_item = self._local_cache[key]
            if cache_item['expires_at'] > datetime.now():
                return cache_item['value']
            else:
                del self._local_cache[key]
        
        # 检查 Redis 缓存
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600, local_cache: bool = True):
        """设置缓存值"""
        try:
            # 设置 Redis 缓存
            if self.redis_client:
                await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            
            # 设置本地缓存（仅对小数据）
            if local_cache and len(str(value)) < 10000:  # 小于10KB
                # 清理过期的本地缓存
                if len(self._local_cache) >= self._local_cache_max_size:
                    self._cleanup_local_cache()
                
                self._local_cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=min(ttl, 300))  # 本地缓存最多5分钟
                }
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        # 删除本地缓存
        self._local_cache.pop(key, None)
        
        # 删除 Redis 缓存
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """按模式删除缓存"""
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis delete pattern error: {e}")
    
    def _cleanup_local_cache(self):
        """清理过期的本地缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self._local_cache.items()
            if item['expires_at'] <= now
        ]
        for key in expired_keys:
            del self._local_cache[key]


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(
    prefix: str,
    ttl: int = 3600,
    key_func: Optional[callable] = None,
    local_cache: bool = True
):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_cache_key(prefix, *args, **kwargs)
            
            # 尝试获取缓存
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            if result is not None:
                await cache_manager.set(cache_key, result, ttl, local_cache)
            
            return result
        return wrapper
    return decorator


class CacheKeys:
    """缓存键常量"""
    USER_PROFILE = "user:profile"
    USER_SOURCES = "user:sources"
    USER_PREFERENCES = "user:preferences"
    DAILY_DIGEST = "daily:digest"
    ITEM_SUMMARY = "item:summary"
    POPULAR_ITEMS = "popular:items"
    SOURCE_CONTENT = "source:content"
    SEARCH_RESULTS = "search:results"


class CacheTTL:
    """缓存过期时间常量（秒）"""
    SHORT = 300      # 5分钟
    MEDIUM = 1800    # 30分钟
    LONG = 3600      # 1小时
    VERY_LONG = 86400  # 24小时


# 具体缓存函数示例
@cached(CacheKeys.USER_PROFILE, CacheTTL.MEDIUM)
async def get_user_profile_cached(user_id: str):
    """获取用户配置（缓存版本）"""
    # 这里应该调用实际的数据库查询
    pass


@cached(CacheKeys.DAILY_DIGEST, CacheTTL.LONG, key_func=lambda user_id, date: f"daily:digest:{user_id}:{date}")
async def get_daily_digest_cached(user_id: str, date: str):
    """获取每日摘要（缓存版本）"""
    pass


async def invalidate_user_cache(user_id: str):
    """失效用户相关缓存"""
    patterns = [
        f"*{CacheKeys.USER_PROFILE}*{user_id}*",
        f"*{CacheKeys.USER_SOURCES}*{user_id}*",
        f"*{CacheKeys.USER_PREFERENCES}*{user_id}*",
        f"*{CacheKeys.DAILY_DIGEST}*{user_id}*",
    ]
    
    for pattern in patterns:
        await cache_manager.delete_pattern(pattern)


async def warm_cache():
    """缓存预热"""
    logger.info("Starting cache warm-up")
    
    # 预加载热门内容
    # await get_popular_items_cached()
    
    # 预加载活跃用户的数据
    # active_users = await get_active_users()
    # for user in active_users:
    #     await get_user_profile_cached(user.id)
    
    logger.info("Cache warm-up completed")


# 缓存监控函数
async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    stats = {
        "local_cache_size": len(cache_manager._local_cache),
        "redis_connected": cache_manager.redis_client is not None
    }
    
    if cache_manager.redis_client:
        try:
            info = await cache_manager.redis_client.info()
            stats.update({
                "redis_memory_used": info.get("used_memory_human"),
                "redis_connected_clients": info.get("connected_clients"),
                "redis_keyspace_hits": info.get("keyspace_hits"),
                "redis_keyspace_misses": info.get("keyspace_misses"),
            })
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
    
    return stats