"""
Performance optimization - Linus style: Measure, don't guess.
"Premature optimization is the root of all evil, but lazy coding is worse."
"""

import time
import logging
from functools import wraps
from typing import Callable, Any
import gc

logger = logging.getLogger(__name__)


def timed(func: Callable) -> Callable:
    """Simple timing decorator - measure, log, done"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            if elapsed > 1.0:  # Only log slow operations
                logger.warning(f"{func.__name__} took {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            if elapsed > 1.0:
                logger.warning(f"{func.__name__} took {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    
    # Return appropriate wrapper
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class SimpleCache:
    """Dead simple in-memory cache - no Redis complexity"""
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        """Get from cache if valid"""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # Expired - remove it
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set in cache - LRU eviction if needed"""
        # Simple size limit
        if len(self.cache) >= self.max_size:
            # Remove oldest
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear the cache"""
        self.cache.clear()
        self.timestamps.clear()
        gc.collect()  # Help the garbage collector


# Global cache instance - one cache to rule them all
_cache = SimpleCache()


def cached(ttl: int = 3600):
    """Cache decorator - simple key generation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simple cache key - function name + args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            result = _cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# Performance settings - no auto-tuning nonsense
PERFORMANCE_CONFIG = {
    'db_pool_size': 10,  # Fixed, reasonable default
    'db_max_overflow': 20,
    'request_timeout': 30,
    'cache_ttl': 3600,
    'max_content_length': 10 * 1024 * 1024,  # 10MB
    'batch_size': 100,
    'max_workers': 4,  # For any threading needs
}