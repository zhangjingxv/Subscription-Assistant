"""
Performance tuning - Linus style: measure, optimize, validate
"Premature optimization is the root of all evil, but mature optimization is essential."
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import wraps
import structlog

logger = structlog.get_logger()


@dataclass
class PerformanceProfile:
    """Performance profile for different deployment scenarios"""
    name: str
    max_workers: int
    connection_pool_size: int
    request_timeout: float
    memory_limit_mb: int
    cpu_limit_percent: float
    cache_size: int


class PerformanceTuner:
    """Intelligent performance tuner - adapts to hardware and load"""
    
    def __init__(self):
        self.profiles = self._create_profiles()
        self.current_profile = self._detect_optimal_profile()
        self.metrics_history = []
        
    def _create_profiles(self) -> Dict[str, PerformanceProfile]:
        """Create performance profiles for different scenarios"""
        return {
            "minimal": PerformanceProfile(
                name="minimal",
                max_workers=1,
                connection_pool_size=10,
                request_timeout=30.0,
                memory_limit_mb=128,
                cpu_limit_percent=50.0,
                cache_size=100
            ),
            
            "development": PerformanceProfile(
                name="development", 
                max_workers=2,
                connection_pool_size=20,
                request_timeout=60.0,
                memory_limit_mb=256,
                cpu_limit_percent=70.0,
                cache_size=500
            ),
            
            "production": PerformanceProfile(
                name="production",
                max_workers=4,
                connection_pool_size=50,
                request_timeout=30.0,
                memory_limit_mb=512,
                cpu_limit_percent=80.0,
                cache_size=1000
            ),
            
            "high_performance": PerformanceProfile(
                name="high_performance",
                max_workers=8,
                connection_pool_size=100,
                request_timeout=15.0,
                memory_limit_mb=1024,
                cpu_limit_percent=90.0,
                cache_size=2000
            )
        }
    
    def _detect_optimal_profile(self) -> PerformanceProfile:
        """Detect optimal performance profile based on system"""
        try:
            import psutil
            
            # Get system info
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # Environment detection
            environment = os.getenv("ENVIRONMENT", "development")
            
            if environment == "production":
                if cpu_count >= 4 and memory_gb >= 4:
                    return self.profiles["high_performance"]
                else:
                    return self.profiles["production"]
            else:
                if cpu_count >= 2 and memory_gb >= 2:
                    return self.profiles["development"]
                else:
                    return self.profiles["minimal"]
                    
        except ImportError:
            logger.info("psutil not available, using minimal profile")
            return self.profiles["minimal"]
    
    def get_uvicorn_config(self) -> Dict[str, Any]:
        """Get optimized uvicorn configuration"""
        profile = self.current_profile
        
        config = {
            "workers": 1,  # Single worker for simplicity
            "loop": "uvloop" if self._is_uvloop_available() else "asyncio",
            "http": "httptools" if self._is_httptools_available() else "h11",
            "access_log": os.getenv("ENVIRONMENT") == "development",
            "timeout_keep_alive": 5,
            "timeout_graceful_shutdown": 10,
            "limit_concurrency": profile.connection_pool_size,
            "limit_max_requests": 1000,
        }
        
        logger.info("Performance configuration", profile=profile.name, **config)
        return config
    
    def _is_uvloop_available(self) -> bool:
        """Check if uvloop is available for better performance"""
        try:
            import uvloop
            return True
        except ImportError:
            return False
    
    def _is_httptools_available(self) -> bool:
        """Check if httptools is available for better HTTP parsing"""
        try:
            import httptools
            return True
        except ImportError:
            return False
    
    def get_aiohttp_config(self) -> Dict[str, Any]:
        """Get optimized aiohttp configuration"""
        profile = self.current_profile
        
        return {
            "connector_limit": profile.connection_pool_size,
            "connector_limit_per_host": profile.connection_pool_size // 4,
            "timeout_total": profile.request_timeout,
            "timeout_connect": 10.0,
            "timeout_sock_read": 10.0,
        }
    
    def optimize_async_settings(self):
        """Optimize asyncio settings for better performance"""
        try:
            # Set optimal asyncio policy
            if sys.platform == "linux" and self._is_uvloop_available():
                import uvloop
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                logger.info("✅ uvloop enabled for better performance")
            
            # Optimize garbage collection for async workloads
            import gc
            gc.set_threshold(700, 10, 10)  # More aggressive GC for async
            
        except Exception as e:
            logger.warning("Performance optimization failed", error=str(e))


def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time > 1.0:
                logger.warning(
                    "Slow operation detected",
                    function=func.__name__,
                    execution_time=execution_time
                )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Operation failed",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e)
            )
            raise
    
    return wrapper


class AdaptiveCache:
    """Adaptive cache that adjusts size based on memory pressure"""
    
    def __init__(self, initial_size: int = 100):
        self.cache = {}
        self.access_times = {}
        self.max_size = initial_size
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get from cache with LRU tracking"""
        if key in self.cache:
            self.access_times[key] = time.time()
            self.hit_count += 1
            return self.cache[key]
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set cache value with intelligent eviction"""
        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / max(total_requests, 1)
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count
        }
    
    def adapt_size(self, memory_usage_mb: float):
        """Adapt cache size based on memory pressure"""
        if memory_usage_mb > 400:  # High memory usage
            self.max_size = max(50, self.max_size // 2)
            logger.info("Cache size reduced due to memory pressure", new_size=self.max_size)
        elif memory_usage_mb < 100:  # Low memory usage
            self.max_size = min(1000, self.max_size * 2)
            logger.debug("Cache size increased", new_size=self.max_size)


# Global instances
_performance_tuner = PerformanceTuner()
_adaptive_cache = AdaptiveCache()


def get_performance_tuner() -> PerformanceTuner:
    """Get global performance tuner"""
    return _performance_tuner


def get_adaptive_cache() -> AdaptiveCache:
    """Get global adaptive cache"""
    return _adaptive_cache


def optimize_for_environment():
    """Optimize settings for current environment"""
    tuner = get_performance_tuner()
    
    # Apply asyncio optimizations
    tuner.optimize_async_settings()
    
    # Log current profile
    profile = tuner.current_profile
    logger.info(
        "Performance profile selected",
        profile=profile.name,
        workers=profile.max_workers,
        memory_limit=profile.memory_limit_mb,
        cpu_limit=profile.cpu_limit_percent
    )
    
    return tuner.get_uvicorn_config()