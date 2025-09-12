"""
生产级结构化日志配置
支持多种输出格式和日志轮转
"""

import sys
import logging
import logging.handlers
from typing import Any, Dict
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory
import json
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
        
        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """上下文过滤器，添加请求相关信息"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 这里可以添加请求ID、用户ID等上下文信息
        # 需要配合中间件使用
        return True


def setup_logging() -> None:
    """设置应用日志配置"""
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.environment == "production":
        # 生产环境使用 JSON 格式
        console_handler.setFormatter(JSONFormatter())
    else:
        # 开发环境使用可读格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # 文件处理器（仅生产环境）
    if settings.environment == "production":
        # 应用日志文件
        app_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "app.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        app_handler.setFormatter(JSONFormatter())
        app_handler.setLevel(logging.INFO)
        root_logger.addHandler(app_handler)
        
        # 错误日志文件
        error_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "error.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # 访问日志文件
        access_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "access.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        access_handler.setFormatter(JSONFormatter())
        
        # 创建访问日志记录器
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
    
    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def setup_structlog() -> None:
    """设置 structlog 配置"""
    
    # 配置 structlog 处理器
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.environment == "production":
        # 生产环境使用 JSON 处理器
        processors.append(structlog.processors.JSONRenderer())
    else:
        # 开发环境使用彩色控制台输出
        processors.extend([
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                          structlog.processors.CallsiteParameter.LINENO]
            ),
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


# 日志中间件
async def logging_middleware(request, call_next):
    """请求日志中间件"""
    import time
    import uuid
    
    # 生成请求ID
    request_id = str(uuid.uuid4())
    
    # 记录请求开始
    start_time = time.time()
    logger = get_logger("access")
    
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        request_id=request_id,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    # 处理请求
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            status_code=response.status_code,
            duration=duration,
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # 记录请求异常
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            duration=duration,
            error=str(e),
            exc_info=True,
        )
        raise


# 业务日志记录器
class BusinessLogger:
    """业务日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("business")
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """记录用户行为"""
        self.logger.info(
            "User action",
            user_id=user_id,
            action=action,
            details=details or {}
        )
    
    def log_content_fetch(self, source_id: str, success: bool, item_count: int = 0, error: str = None):
        """记录内容获取"""
        self.logger.info(
            "Content fetch",
            source_id=source_id,
            success=success,
            item_count=item_count,
            error=error
        )
    
    def log_ai_request(self, service: str, model: str, tokens_used: int, duration: float):
        """记录AI服务请求"""
        self.logger.info(
            "AI request",
            service=service,
            model=model,
            tokens_used=tokens_used,
            duration=duration
        )
    
    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """记录系统事件"""
        self.logger.info(
            "System event",
            event=event,
            details=details or {}
        )


# 全局业务日志记录器实例
business_logger = BusinessLogger()


# 日志配置验证
def validate_logging_config():
    """验证日志配置"""
    issues = []
    
    # 检查日志目录权限
    log_dir = Path("logs")
    if not log_dir.exists():
        try:
            log_dir.mkdir(exist_ok=True)
        except PermissionError:
            issues.append("无法创建日志目录，权限不足")
    
    # 检查磁盘空间
    import shutil
    _, _, free = shutil.disk_usage(log_dir)
    if free < 1024 * 1024 * 1024:  # 1GB
        issues.append("磁盘空间不足，可能影响日志写入")
    
    # 检查日志级别配置
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.log_level.upper() not in valid_levels:
        issues.append(f"无效的日志级别: {settings.log_level}")
    
    return issues


# 初始化日志配置
def init_logging():
    """初始化日志配置"""
    # 验证配置
    issues = validate_logging_config()
    if issues:
        print("日志配置问题:")
        for issue in issues:
            print(f"- {issue}")
    
    # 设置日志
    setup_logging()
    setup_structlog()
    
    # 测试日志
    logger = get_logger("startup")
    logger.info("Logging system initialized", environment=settings.environment)


# 日志性能监控
class LoggingMetrics:
    """日志性能监控"""
    
    def __init__(self):
        self.log_counts = {}
        self.error_counts = {}
    
    def increment_log_count(self, level: str):
        """增加日志计数"""
        self.log_counts[level] = self.log_counts.get(level, 0) + 1
    
    def increment_error_count(self, error_type: str):
        """增加错误计数"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取日志指标"""
        return {
            "log_counts": self.log_counts,
            "error_counts": self.error_counts,
            "total_logs": sum(self.log_counts.values()),
            "total_errors": sum(self.error_counts.values())
        }


# 全局日志指标实例
logging_metrics = LoggingMetrics()