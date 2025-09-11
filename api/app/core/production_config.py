"""
生产环境性能优化配置
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """生产环境专用配置"""
    
    # 数据库连接池优化
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_echo: bool = False
    
    # Redis 连接优化
    redis_max_connections: int = 100
    redis_retry_on_timeout: bool = True
    redis_socket_keepalive: bool = True
    redis_socket_keepalive_options: dict = {
        "TCP_KEEPIDLE": 1,
        "TCP_KEEPINTVL": 3,
        "TCP_KEEPCNT": 5,
    }
    
    # HTTP 客户端优化
    http_timeout: int = 30
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: int = 5
    
    # 缓存配置
    cache_default_ttl: int = 3600  # 1小时
    cache_long_ttl: int = 86400   # 24小时
    cache_short_ttl: int = 300    # 5分钟
    
    # 限流配置
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 100
    
    # 任务队列优化
    celery_worker_concurrency: int = 4
    celery_worker_prefetch_multiplier: int = 1
    celery_worker_max_tasks_per_child: int = 1000
    celery_task_time_limit: int = 1800
    celery_task_soft_time_limit: int = 1500
    
    # 日志配置
    log_format: str = "json"
    log_level: str = "INFO"
    log_rotation: str = "daily"
    log_retention_days: int = 30
    
    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # 安全配置
    cors_allow_origins: list = []
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["GET", "POST", "PUT", "DELETE"]
    cors_allow_headers: list = ["*"]
    
    # 备份配置
    backup_enabled: bool = True
    backup_s3_bucket: Optional[str] = None
    backup_retention_days: int = 30
    backup_schedule: str = "0 2 * * *"  # 每天凌晨2点
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False


@lru_cache()
def get_production_settings() -> ProductionSettings:
    """获取生产环境配置"""
    return ProductionSettings()


def is_production() -> bool:
    """检查是否为生产环境"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


# 性能优化建议
PERFORMANCE_RECOMMENDATIONS = {
    "database": [
        "使用连接池避免频繁建立连接",
        "启用查询缓存减少重复查询",
        "添加适当的数据库索引",
        "定期分析查询性能",
        "考虑读写分离"
    ],
    "caching": [
        "对频繁访问的数据添加缓存",
        "使用 Redis 集群提高可用性",
        "实现缓存预热策略",
        "监控缓存命中率",
        "设置合理的缓存过期时间"
    ],
    "api": [
        "实现响应压缩",
        "使用 HTTP/2",
        "添加 API 限流",
        "实现请求去重",
        "优化 JSON 序列化"
    ],
    "background_tasks": [
        "合理设置任务并发数",
        "实现任务优先级",
        "添加任务重试机制",
        "监控任务队列长度",
        "定期清理过期任务"
    ]
}