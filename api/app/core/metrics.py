"""
应用性能指标收集
"""

import time
import psutil
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from fastapi import Request, Response
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 创建指标注册表
registry = CollectorRegistry()

# HTTP 请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# 数据库指标
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry
)

# 缓存指标
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

# 任务队列指标
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status'],
    registry=registry
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=registry
)

# 业务指标
user_active_total = Counter(
    'user_active_total',
    'Total active users',
    registry=registry
)

content_fetch_total = Counter(
    'content_fetch_total',
    'Total content fetch attempts',
    ['source_type'],
    registry=registry
)

content_fetch_failed_total = Counter(
    'content_fetch_failed_total',
    'Total failed content fetches',
    ['source_type', 'error_type'],
    registry=registry
)

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI service requests',
    ['service', 'model'],
    registry=registry
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI service request duration in seconds',
    ['service', 'model'],
    registry=registry
)

# 系统指标
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=registry
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path'],
    registry=registry
)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent()
            system_cpu_usage.set(cpu_percent)
            
            # 内存使用
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            system_disk_usage.labels(path='/').set(disk.used)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """记录 HTTP 请求指标"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, duration: float):
        """记录数据库查询指标"""
        db_query_duration_seconds.labels(operation=operation).observe(duration)
    
    def record_cache_hit(self, cache_type: str):
        """记录缓存命中"""
        cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """记录缓存未命中"""
        cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_celery_task(self, task_name: str, status: str, duration: float = None):
        """记录 Celery 任务指标"""
        celery_tasks_total.labels(task_name=task_name, status=status).inc()
        
        if duration is not None:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    def record_user_activity(self):
        """记录用户活跃"""
        user_active_total.inc()
    
    def record_content_fetch(self, source_type: str, success: bool = True, error_type: str = None):
        """记录内容获取"""
        content_fetch_total.labels(source_type=source_type).inc()
        
        if not success and error_type:
            content_fetch_failed_total.labels(
                source_type=source_type,
                error_type=error_type
            ).inc()
    
    def record_ai_request(self, service: str, model: str, duration: float):
        """记录 AI 服务请求"""
        ai_requests_total.labels(service=service, model=model).inc()
        ai_request_duration_seconds.labels(service=service, model=model).observe(duration)


# 全局指标收集器实例
metrics = MetricsCollector()


# 装饰器：自动记录函数执行时间
def monitor_execution_time(metric_name: str, labels: Dict[str, str] = None):
    """监控函数执行时间的装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                # 这里可以根据 metric_name 选择合适的指标
                if metric_name == "db_query":
                    metrics.record_db_query(
                        labels.get("operation", "unknown") if labels else "unknown",
                        duration
                    )
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                if metric_name == "db_query":
                    metrics.record_db_query(
                        labels.get("operation", "unknown") if labels else "unknown",
                        duration
                    )
            return result
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    return decorator


# FastAPI 中间件：自动记录 HTTP 指标
async def metrics_middleware(request: Request, call_next):
    """HTTP 请求指标中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # 简化路径（移除参数）
    endpoint = request.url.path
    for route in request.app.routes:
        if hasattr(route, 'path') and route.path == endpoint:
            endpoint = route.path
            break
    
    metrics.record_http_request(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
        duration=duration
    )
    
    return response


# 指标导出端点
async def metrics_endpoint():
    """Prometheus 指标导出端点"""
    # 收集最新的系统指标
    metrics.collect_system_metrics()
    
    # 生成 Prometheus 格式的指标
    data = generate_latest(registry)
    
    return Response(
        content=data,
        media_type=CONTENT_TYPE_LATEST
    )


# 健康检查端点
async def health_check():
    """健康检查端点"""
    try:
        # 检查关键组件状态
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - metrics.start_time,
            "version": "1.0.0"  # 应该从配置中获取
        }
        
        # 可以添加更多健康检查逻辑
        # - 数据库连接检查
        # - Redis 连接检查
        # - 外部服务检查
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }