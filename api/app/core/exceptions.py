"""
统一异常处理和错误响应
提供完整的错误处理机制和用户友好的错误信息
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AttentionSyncException(Exception):
    """AttentionSync 基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AttentionSyncException):
    """数据验证错误"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
            status_code=400
        )


class AuthenticationError(AttentionSyncException):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(AttentionSyncException):
    """授权错误"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


class NotFoundError(AttentionSyncException):
    """资源未找到错误"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )


class ConflictError(AttentionSyncException):
    """资源冲突错误"""
    
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            details={"resource": resource},
            status_code=409
        )


class RateLimitError(AttentionSyncException):
    """限流错误"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
            status_code=429
        )


class ExternalServiceError(AttentionSyncException):
    """外部服务错误"""
    
    def __init__(self, service: str, message: str = None, original_error: str = None):
        message = message or f"{service} service unavailable"
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "original_error": original_error},
            status_code=503
        )


class DatabaseError(AttentionSyncException):
    """数据库错误"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"operation": operation, "table": table},
            status_code=500
        )


class CacheError(AttentionSyncException):
    """缓存错误"""
    
    def __init__(self, message: str, cache_key: str = None):
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details={"cache_key": cache_key},
            status_code=500
        )


class ConfigurationError(AttentionSyncException):
    """配置错误"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key},
            status_code=500
        )


def create_error_response(
    error: Union[AttentionSyncException, Exception],
    request_id: str = None,
    include_traceback: bool = None
) -> Dict[str, Any]:
    """创建标准化的错误响应"""
    
    if include_traceback is None:
        include_traceback = settings.environment == "development"
    
    if isinstance(error, AttentionSyncException):
        response = {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        status_code = error.status_code
    else:
        # 未知异常
        response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        status_code = 500
        
        # 开发环境显示详细错误信息
        if settings.environment == "development":
            response["error"]["message"] = str(error)
            response["error"]["type"] = type(error).__name__
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()
    
    return response, status_code


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    # 记录错误日志
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    # 创建标准化响应
    response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """验证异常处理器"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    # 提取验证错误详情
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    # 记录错误日志
    logger.warning(
        f"Validation Error: {len(errors)} errors",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )
    
    response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=422,
        content=response
    )


async def attentionsync_exception_handler(request: Request, exc: AttentionSyncException):
    """AttentionSync 异常处理器"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    # 记录错误日志
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        f"AttentionSync Exception: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.code,
            "details": exc.details
        }
    )
    
    response, status_code = create_error_response(exc, request_id)
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    # 记录错误日志
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    response, status_code = create_error_response(exc, request_id)
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )


def register_exception_handlers(app):
    """注册异常处理器"""
    
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AttentionSyncException, attentionsync_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


# 错误处理装饰器
def handle_exceptions(
    default_message: str = "An error occurred",
    log_level: int = logging.ERROR,
    reraise: bool = False
):
    """异常处理装饰器"""
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AttentionSyncException:
                # 重新抛出 AttentionSync 异常
                raise
            except Exception as e:
                logger.log(log_level, f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise
                raise AttentionSyncException(default_message) from e
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AttentionSyncException:
                raise
            except Exception as e:
                logger.log(log_level, f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise
                raise AttentionSyncException(default_message) from e
        
        # 返回适当的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 错误统计
class ErrorStats:
    """错误统计"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_rates = {}
    
    def record_error(self, error_code: str, path: str = None):
        """记录错误"""
        key = f"{error_code}:{path}" if path else error_code
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "top_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


# 全局错误统计实例
error_stats = ErrorStats()


# 健康检查相关异常
class HealthCheckError(AttentionSyncException):
    """健康检查错误"""
    
    def __init__(self, component: str, message: str):
        super().__init__(
            message=f"{component} health check failed: {message}",
            code="HEALTH_CHECK_ERROR",
            details={"component": component},
            status_code=503
        )