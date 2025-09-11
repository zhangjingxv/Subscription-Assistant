"""
异常处理模块测试
"""

import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from app.core.exceptions import (
    AttentionSyncException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    DatabaseError,
    CacheError,
    ConfigurationError,
    create_error_response,
    http_exception_handler,
    validation_exception_handler,
    attentionsync_exception_handler,
    general_exception_handler,
    handle_exceptions,
    ErrorStats,
    HealthCheckError
)


class TestAttentionSyncException:
    """测试基础异常类"""
    
    def test_basic_exception(self):
        """测试基础异常创建"""
        exc = AttentionSyncException("Test error")
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}
    
    def test_exception_with_details(self):
        """测试带详情的异常"""
        details = {"field": "test", "value": "invalid"}
        exc = AttentionSyncException(
            "Test error",
            code="TEST_ERROR",
            details=details,
            status_code=400
        )
        
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == details


class TestSpecificExceptions:
    """测试特定异常类"""
    
    def test_validation_error(self):
        """测试验证错误"""
        exc = ValidationError("Invalid field", field="email")
        
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details["field"] == "email"
    
    def test_authentication_error(self):
        """测试认证错误"""
        exc = AuthenticationError()
        
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
        assert "Authentication failed" in exc.message
    
    def test_authorization_error(self):
        """测试授权错误"""
        exc = AuthorizationError()
        
        assert exc.code == "AUTHORIZATION_ERROR"
        assert exc.status_code == 403
        assert "Access denied" in exc.message
    
    def test_not_found_error(self):
        """测试资源未找到错误"""
        exc = NotFoundError("User", "123")
        
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == 404
        assert "User not found: 123" in exc.message
        assert exc.details["resource"] == "User"
        assert exc.details["identifier"] == "123"
    
    def test_conflict_error(self):
        """测试冲突错误"""
        exc = ConflictError("Email already exists", resource="User")
        
        assert exc.code == "CONFLICT_ERROR"
        assert exc.status_code == 409
        assert exc.details["resource"] == "User"
    
    def test_rate_limit_error(self):
        """测试限流错误"""
        exc = RateLimitError(retry_after=60)
        
        assert exc.code == "RATE_LIMIT_ERROR"
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60
    
    def test_external_service_error(self):
        """测试外部服务错误"""
        exc = ExternalServiceError("OpenAI", "API quota exceeded")
        
        assert exc.code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 503
        assert exc.details["service"] == "OpenAI"
    
    def test_database_error(self):
        """测试数据库错误"""
        exc = DatabaseError("Connection failed", operation="SELECT", table="users")
        
        assert exc.code == "DATABASE_ERROR"
        assert exc.status_code == 500
        assert exc.details["operation"] == "SELECT"
        assert exc.details["table"] == "users"
    
    def test_cache_error(self):
        """测试缓存错误"""
        exc = CacheError("Redis connection failed", cache_key="user:123")
        
        assert exc.code == "CACHE_ERROR"
        assert exc.status_code == 500
        assert exc.details["cache_key"] == "user:123"
    
    def test_configuration_error(self):
        """测试配置错误"""
        exc = ConfigurationError("Missing API key", config_key="OPENAI_API_KEY")
        
        assert exc.code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500
        assert exc.details["config_key"] == "OPENAI_API_KEY"
    
    def test_health_check_error(self):
        """测试健康检查错误"""
        exc = HealthCheckError("database", "Connection timeout")
        
        assert exc.code == "HEALTH_CHECK_ERROR"
        assert exc.status_code == 503
        assert "database health check failed" in exc.message
        assert exc.details["component"] == "database"


class TestErrorResponse:
    """测试错误响应创建"""
    
    def test_create_error_response_with_attentionsync_exception(self):
        """测试创建 AttentionSync 异常响应"""
        exc = ValidationError("Invalid email", field="email")
        response, status_code = create_error_response(exc, request_id="test-123")
        
        assert status_code == 400
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid email"
        assert response["error"]["details"]["field"] == "email"
        assert response["error"]["request_id"] == "test-123"
        assert "timestamp" in response["error"]
    
    def test_create_error_response_with_generic_exception(self):
        """测试创建通用异常响应"""
        exc = ValueError("Invalid value")
        response, status_code = create_error_response(exc)
        
        assert status_code == 500
        assert response["error"]["code"] == "INTERNAL_ERROR"
        assert response["error"]["message"] == "An internal error occurred"
    
    def test_create_error_response_development_mode(self, monkeypatch):
        """测试开发模式下的错误响应"""
        # Mock 开发环境
        from app.core import config
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        monkeypatch.setattr(config, "get_settings", lambda: mock_settings)
        
        exc = ValueError("Invalid value")
        response, status_code = create_error_response(exc, include_traceback=True)
        
        assert "traceback" in response["error"]
        assert response["error"]["message"] == "Invalid value"
        assert response["error"]["type"] == "ValueError"


@pytest.mark.asyncio
class TestExceptionHandlers:
    """测试异常处理器"""
    
    async def test_http_exception_handler(self):
        """测试 HTTP 异常处理器"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.state = MagicMock()
        request.state.request_id = "test-123"
        
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await http_exception_handler(request, exc)
        
        assert response.status_code == 404
        response_data = response.body.decode()
        import json
        data = json.loads(response_data)
        
        assert data["error"]["code"] == "HTTP_404"
        assert data["error"]["message"] == "Not found"
        assert data["error"]["request_id"] == "test-123"
    
    async def test_validation_exception_handler(self):
        """测试验证异常处理器"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.state = MagicMock()
        request.state.request_id = "test-123"
        
        # 创建验证错误
        from pydantic import ValidationError as PydanticValidationError
        try:
            from pydantic import BaseModel, Field
            
            class TestModel(BaseModel):
                email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
                age: int = Field(..., gt=0)
            
            TestModel(email="invalid-email", age=-1)
        except PydanticValidationError as e:
            exc = RequestValidationError(e.errors())
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == 422
        response_data = response.body.decode()
        import json
        data = json.loads(response_data)
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Request validation failed"
        assert "errors" in data["error"]["details"]
        assert len(data["error"]["details"]["errors"]) > 0
    
    async def test_attentionsync_exception_handler(self):
        """测试 AttentionSync 异常处理器"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.state = MagicMock()
        request.state.request_id = "test-123"
        
        exc = ValidationError("Invalid data", field="email")
        
        response = await attentionsync_exception_handler(request, exc)
        
        assert response.status_code == 400
        response_data = response.body.decode()
        import json
        data = json.loads(response_data)
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Invalid data"
        assert data["error"]["details"]["field"] == "email"
    
    async def test_general_exception_handler(self):
        """测试通用异常处理器"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.state = MagicMock()
        request.state.request_id = "test-123"
        
        exc = ValueError("Something went wrong")
        
        response = await general_exception_handler(request, exc)
        
        assert response.status_code == 500
        response_data = response.body.decode()
        import json
        data = json.loads(response_data)
        
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "An internal error occurred"


class TestHandleExceptionsDecorator:
    """测试异常处理装饰器"""
    
    def test_sync_function_success(self):
        """测试同步函数成功执行"""
        @handle_exceptions("Custom error")
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_sync_function_attentionsync_exception(self):
        """测试同步函数 AttentionSync 异常"""
        @handle_exceptions("Custom error")
        def test_func():
            raise ValidationError("Test validation error")
        
        with pytest.raises(ValidationError):
            test_func()
    
    def test_sync_function_generic_exception(self):
        """测试同步函数通用异常"""
        @handle_exceptions("Custom error")
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(AttentionSyncException) as exc_info:
            test_func()
        
        assert str(exc_info.value) == "Custom error"
    
    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """测试异步函数成功执行"""
        @handle_exceptions("Custom error")
        async def test_func(x):
            return x * 2
        
        result = await test_func(5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_async_function_exception(self):
        """测试异步函数异常"""
        @handle_exceptions("Custom error")
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(AttentionSyncException) as exc_info:
            await test_func()
        
        assert str(exc_info.value) == "Custom error"
    
    def test_reraise_option(self):
        """测试重新抛出选项"""
        @handle_exceptions("Custom error", reraise=True)
        def test_func():
            raise ValueError("Original error")
        
        with pytest.raises(ValueError):
            test_func()


class TestErrorStats:
    """测试错误统计"""
    
    def test_record_error(self):
        """测试记录错误"""
        stats = ErrorStats()
        
        stats.record_error("VALIDATION_ERROR", "/api/users")
        stats.record_error("VALIDATION_ERROR", "/api/users")
        stats.record_error("NOT_FOUND", "/api/posts")
        
        error_stats = stats.get_error_stats()
        
        assert error_stats["total_errors"] == 3
        assert error_stats["error_counts"]["VALIDATION_ERROR:/api/users"] == 2
        assert error_stats["error_counts"]["NOT_FOUND:/api/posts"] == 1
        
        # 检查 top_errors
        top_errors = error_stats["top_errors"]
        assert len(top_errors) == 2
        assert top_errors[0][0] == "VALIDATION_ERROR:/api/users"
        assert top_errors[0][1] == 2
    
    def test_record_error_without_path(self):
        """测试记录不带路径的错误"""
        stats = ErrorStats()
        
        stats.record_error("INTERNAL_ERROR")
        
        error_stats = stats.get_error_stats()
        
        assert error_stats["total_errors"] == 1
        assert error_stats["error_counts"]["INTERNAL_ERROR"] == 1