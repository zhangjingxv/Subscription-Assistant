"""
全球化性能优化系统
包含多层缓存、CDN集成、数据库优化等
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from dataclasses import dataclass
import json
import hashlib

import aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.global_config import get_global_config, Region
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600  # 默认1小时
    prefix: str = "attentionsync"
    region: Optional[str] = None
    compression: bool = True
    serializer: str = "json"  # json, pickle, msgpack


@dataclass
class PerformanceMetrics:
    """性能指标"""
    request_count: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    db_queries: int = 0
    db_query_time: float = 0.0
    
    @property
    def avg_response_time(self) -> float:
        return self.total_response_time / max(self.request_count, 1)
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total, 1)


class MultiLayerCache:
    """多层缓存系统"""
    
    def __init__(self):
        self.redis_clients: Dict[str, aioredis.Redis] = {}
        self.local_cache: Dict[str, Dict] = {}
        self.config_manager = get_global_config()
        self.metrics = PerformanceMetrics()
    
    async def init_redis_clients(self):
        """初始化Redis客户端"""
        for region, redis_url in self.config_manager.settings.redis_clusters.items():
            try:
                client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True
                )
                await client.ping()
                self.redis_clients[region] = client
                logger.info(f"Redis client initialized for region: {region}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client for {region}: {e}")
    
    def _generate_cache_key(self, key: str, region: str = "global", prefix: str = "attentionsync") -> str:
        """生成缓存键"""
        return f"{prefix}:{region}:{key}"
    
    def _serialize_value(self, value: Any, serializer: str = "json") -> str:
        """序列化值"""
        if serializer == "json":
            return json.dumps(value, ensure_ascii=False, default=str)
        # 可以扩展支持其他序列化方式
        return str(value)
    
    def _deserialize_value(self, value: str, serializer: str = "json") -> Any:
        """反序列化值"""
        if serializer == "json":
            return json.loads(value)
        return value
    
    async def get(self, key: str, region: str = "global", config: CacheConfig = None) -> Optional[Any]:
        """获取缓存值"""
        if config is None:
            config = CacheConfig()
        
        cache_key = self._generate_cache_key(key, region, config.prefix)
        
        # 1. 尝试本地缓存
        local_data = self.local_cache.get(cache_key)
        if local_data and local_data.get('expires_at', 0) > time.time():
            self.metrics.cache_hits += 1
            return local_data['value']
        
        # 2. 尝试Redis缓存
        redis_client = self.redis_clients.get(region)
        if redis_client:
            try:
                cached_value = await redis_client.get(cache_key)
                if cached_value:
                    self.metrics.cache_hits += 1
                    value = self._deserialize_value(cached_value, config.serializer)
                    
                    # 更新本地缓存
                    self.local_cache[cache_key] = {
                        'value': value,
                        'expires_at': time.time() + min(config.ttl, 300)  # 本地缓存最多5分钟
                    }
                    
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        self.metrics.cache_misses += 1
        return None
    
    async def set(self, key: str, value: Any, region: str = "global", config: CacheConfig = None) -> bool:
        """设置缓存值"""
        if config is None:
            config = CacheConfig()
        
        cache_key = self._generate_cache_key(key, region, config.prefix)
        serialized_value = self._serialize_value(value, config.serializer)
        
        # 1. 设置本地缓存
        self.local_cache[cache_key] = {
            'value': value,
            'expires_at': time.time() + min(config.ttl, 300)
        }
        
        # 2. 设置Redis缓存
        redis_client = self.redis_clients.get(region)
        if redis_client:
            try:
                await redis_client.setex(cache_key, config.ttl, serialized_value)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        return False
    
    async def delete(self, key: str, region: str = "global", config: CacheConfig = None) -> bool:
        """删除缓存"""
        if config is None:
            config = CacheConfig()
        
        cache_key = self._generate_cache_key(key, region, config.prefix)
        
        # 删除本地缓存
        self.local_cache.pop(cache_key, None)
        
        # 删除Redis缓存
        redis_client = self.redis_clients.get(region)
        if redis_client:
            try:
                await redis_client.delete(cache_key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        return False
    
    async def clear_region(self, region: str) -> bool:
        """清空区域缓存"""
        redis_client = self.redis_clients.get(region)
        if redis_client:
            try:
                pattern = f"attentionsync:{region}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                
                # 清理本地缓存
                keys_to_remove = [k for k in self.local_cache.keys() if f":{region}:" in k]
                for key in keys_to_remove:
                    del self.local_cache[key]
                
                return True
            except Exception as e:
                logger.error(f"Redis clear region error: {e}")
        
        return False


class DatabaseOptimizer:
    """数据库性能优化器"""
    
    def __init__(self):
        self.query_cache = {}
        self.slow_query_threshold = 1.0  # 1秒
        self.metrics = PerformanceMetrics()
    
    async def execute_with_cache(self, session: AsyncSession, query: str, params: Dict = None, 
                                cache_ttl: int = 300) -> Any:
        """执行带缓存的查询"""
        if params is None:
            params = {}
        
        # 生成查询缓存键
        query_hash = hashlib.md5(f"{query}:{json.dumps(params, sort_keys=True)}".encode()).hexdigest()
        cache_key = f"query:{query_hash}"
        
        # 检查缓存
        cache = get_cache()
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 执行查询
        start_time = time.time()
        try:
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            # 转换为可序列化的格式
            serializable_result = [dict(row._mapping) for row in rows]
            
            execution_time = time.time() - start_time
            self.metrics.db_queries += 1
            self.metrics.db_query_time += execution_time
            
            # 记录慢查询
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")
            
            # 缓存结果
            await cache.set(cache_key, serializable_result, config=CacheConfig(ttl=cache_ttl))
            
            return serializable_result
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    def optimize_query(self, query: str) -> str:
        """优化SQL查询"""
        # 简单的查询优化建议
        optimizations = []
        
        if "SELECT *" in query.upper():
            optimizations.append("Consider selecting specific columns instead of *")
        
        if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
            optimizations.append("Consider adding LIMIT clause to ORDER BY queries")
        
        if len(optimizations) > 0:
            logger.info(f"Query optimization suggestions: {', '.join(optimizations)}")
        
        return query


class CDNManager:
    """CDN管理器"""
    
    def __init__(self):
        self.config_manager = get_global_config()
    
    def get_cdn_url(self, path: str, region: str = "global") -> str:
        """获取CDN URL"""
        base_url = self.config_manager.get_cdn_endpoint(Region(region))
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    
    def get_optimized_image_url(self, image_path: str, width: int = None, 
                               height: int = None, quality: int = 85, 
                               format: str = "webp", region: str = "global") -> str:
        """获取优化后的图片URL"""
        params = []
        
        if width:
            params.append(f"w={width}")
        if height:
            params.append(f"h={height}")
        if quality != 85:
            params.append(f"q={quality}")
        if format != "webp":
            params.append(f"f={format}")
        
        query_string = "&".join(params)
        base_url = self.get_cdn_url(image_path, region)
        
        return f"{base_url}?{query_string}" if query_string else base_url


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.metrics = PerformanceMetrics()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过监控路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # 添加性能相关的请求头
        request.state.start_time = start_time
        request.state.region = self._detect_region(request)
        
        try:
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            self.metrics.request_count += 1
            self.metrics.total_response_time += response_time
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Region"] = request.state.region
            response.headers["X-Cache-Status"] = getattr(request.state, "cache_status", "MISS")
            
            # 记录慢请求
            if response_time > 2.0:
                logger.warning(f"Slow request: {response_time:.2f}s - {request.method} {request.url.path}")
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Request error after {response_time:.2f}s: {e}")
            raise
    
    def _detect_region(self, request: Request) -> str:
        """检测用户区域"""
        # 从请求头检测
        cf_region = request.headers.get("CF-IPCountry", "").upper()
        accept_language = request.headers.get("Accept-Language", "")
        
        config_manager = get_global_config()
        region = config_manager.get_user_region("", accept_language)
        
        return region.value


# 缓存装饰器
def cached(ttl: int = 3600, region: str = "global", prefix: str = "func"):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{prefix}:{hashlib.md5(':'.join(key_parts).encode()).hexdigest()}"
            
            cache = get_cache()
            config = CacheConfig(ttl=ttl, prefix=prefix)
            
            # 尝试从缓存获取
            cached_result = await cache.get(cache_key, region, config)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache.set(cache_key, result, region, config)
            
            return result
        
        return wrapper
    return decorator


# 全局实例
_cache_instance = None
_db_optimizer_instance = None
_cdn_manager_instance = None


def get_cache() -> MultiLayerCache:
    """获取缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLayerCache()
    return _cache_instance


def get_db_optimizer() -> DatabaseOptimizer:
    """获取数据库优化器实例"""
    global _db_optimizer_instance
    if _db_optimizer_instance is None:
        _db_optimizer_instance = DatabaseOptimizer()
    return _db_optimizer_instance


def get_cdn_manager() -> CDNManager:
    """获取CDN管理器实例"""
    global _cdn_manager_instance
    if _cdn_manager_instance is None:
        _cdn_manager_instance = CDNManager()
    return _cdn_manager_instance


async def init_performance_system():
    """初始化性能系统"""
    cache = get_cache()
    await cache.init_redis_clients()
    logger.info("Performance optimization system initialized")


# 性能监控工具函数
async def get_system_metrics() -> Dict[str, Any]:
    """获取系统性能指标"""
    cache = get_cache()
    db_optimizer = get_db_optimizer()
    
    return {
        "cache_metrics": {
            "hits": cache.metrics.cache_hits,
            "misses": cache.metrics.cache_misses,
            "hit_rate": cache.metrics.cache_hit_rate,
        },
        "database_metrics": {
            "queries": db_optimizer.metrics.db_queries,
            "total_time": db_optimizer.metrics.db_query_time,
            "avg_time": db_optimizer.metrics.db_query_time / max(db_optimizer.metrics.db_queries, 1),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }