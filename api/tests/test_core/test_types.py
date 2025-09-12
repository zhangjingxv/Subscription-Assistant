"""
类型系统测试
"""

import pytest
from typing import List, Dict, Union, Optional
from datetime import datetime, date
import uuid

from app.core.types import (
    # 枚举
    Environment, ContentType, SourceType, TaskStatus, UserRole, LogLevel,
    
    # 数据类
    ProcessingResult, PaginationParams, SortParams,
    
    # 响应类型
    APIResponse, PaginatedResponse, ErrorResponse,
    
    # 工具类
    TypeChecker, DataConverter, TypedConfig,
    
    # 装饰器
    type_checked
)


class TestEnums:
    """测试枚举类型"""
    
    def test_environment_enum(self):
        """测试环境枚举"""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.TESTING == "testing"
        assert Environment.PRODUCTION == "production"
        
        # 测试枚举值
        assert len(Environment) == 3
        assert "development" in [e.value for e in Environment]
    
    def test_content_type_enum(self):
        """测试内容类型枚举"""
        assert ContentType.ARTICLE == "article"
        assert ContentType.VIDEO == "video"
        assert ContentType.AUDIO == "audio"
        assert ContentType.IMAGE == "image"
        assert ContentType.DOCUMENT == "document"
    
    def test_source_type_enum(self):
        """测试信息源类型枚举"""
        assert SourceType.RSS == "rss"
        assert SourceType.API == "api"
        assert SourceType.WEBHOOK == "webhook"
        assert SourceType.MANUAL == "manual"
        assert SourceType.SCRAPING == "scraping"
    
    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
    
    def test_user_role_enum(self):
        """测试用户角色枚举"""
        assert UserRole.USER == "user"
        assert UserRole.PREMIUM == "premium"
        assert UserRole.ADMIN == "admin"
        assert UserRole.SUPER_ADMIN == "super_admin"
    
    def test_log_level_enum(self):
        """测试日志级别枚举"""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestDataClasses:
    """测试数据类"""
    
    def test_processing_result(self):
        """测试处理结果数据类"""
        result = ProcessingResult(
            success=True,
            message="Operation completed",
            data={"key": "value"},
            duration=1.5
        )
        
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.data == {"key": "value"}
        assert result.duration == 1.5
        assert result.errors is None
        assert result.metadata is None
    
    def test_processing_result_with_errors(self):
        """测试带错误的处理结果"""
        result = ProcessingResult(
            success=False,
            message="Operation failed",
            errors=["Error 1", "Error 2"]
        )
        
        assert result.success is False
        assert result.errors == ["Error 1", "Error 2"]
    
    def test_pagination_params(self):
        """测试分页参数"""
        params = PaginationParams(page=2, size=10)
        
        assert params.page == 2
        assert params.size == 10
        assert params.offset == 10  # (2-1) * 10
        assert params.limit == 10
    
    def test_pagination_params_defaults(self):
        """测试分页参数默认值"""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0
        assert params.limit == 20
    
    def test_sort_params(self):
        """测试排序参数"""
        params = SortParams(field="created_at", direction="asc")
        
        assert params.field == "created_at"
        assert params.direction == "asc"
    
    def test_sort_params_default_direction(self):
        """测试排序参数默认方向"""
        params = SortParams(field="name")
        
        assert params.field == "name"
        assert params.direction == "desc"


class TestResponseTypes:
    """测试响应类型"""
    
    def test_api_response_success(self):
        """测试成功的 API 响应"""
        response = APIResponse[str](
            success=True,
            message="Success",
            data="test data"
        )
        
        assert response.success is True
        assert response.message == "Success"
        assert response.data == "test data"
        assert response.errors is None
        assert isinstance(response.timestamp, datetime)
    
    def test_api_response_with_errors(self):
        """测试带错误的 API 响应"""
        response = APIResponse[None](
            success=False,
            message="Failed",
            errors=["Error 1", "Error 2"]
        )
        
        assert response.success is False
        assert response.errors == ["Error 1", "Error 2"]
        assert response.data is None
    
    def test_paginated_response(self):
        """测试分页响应"""
        items = ["item1", "item2", "item3"]
        response = PaginatedResponse[str](
            items=items,
            total=100,
            page=2,
            size=10
        )
        
        assert response.items == items
        assert response.total == 100
        assert response.page == 2
        assert response.size == 10
        assert response.pages == 10  # ceil(100/10)
        assert response.has_next is True
        assert response.has_prev is True
    
    def test_paginated_response_first_page(self):
        """测试第一页分页响应"""
        response = PaginatedResponse[str](
            items=["item1"],
            total=50,
            page=1,
            size=10
        )
        
        assert response.pages == 5
        assert response.has_next is True
        assert response.has_prev is False
    
    def test_paginated_response_last_page(self):
        """测试最后一页分页响应"""
        response = PaginatedResponse[str](
            items=["item1"],
            total=50,
            page=5,
            size=10
        )
        
        assert response.has_next is False
        assert response.has_prev is True
    
    def test_error_response(self):
        """测试错误响应"""
        response = ErrorResponse(
            error={
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "details": {"field": "email"}
            }
        )
        
        assert response.success is False
        assert response.error["code"] == "VALIDATION_ERROR"
        assert response.error["message"] == "Invalid input"
        assert response.error["details"]["field"] == "email"
        assert isinstance(response.timestamp, datetime)


class TestTypeChecker:
    """测试类型检查器"""
    
    def test_check_basic_types(self):
        """测试基础类型检查"""
        assert TypeChecker.check_type("hello", str) is True
        assert TypeChecker.check_type(123, int) is True
        assert TypeChecker.check_type(3.14, float) is True
        assert TypeChecker.check_type(True, bool) is True
        
        assert TypeChecker.check_type("hello", int) is False
        assert TypeChecker.check_type(123, str) is False
    
    def test_check_list_types(self):
        """测试列表类型检查"""
        assert TypeChecker.check_type([1, 2, 3], List[int]) is True
        assert TypeChecker.check_type(["a", "b"], List[str]) is True
        assert TypeChecker.check_type([], List[int]) is True
        
        assert TypeChecker.check_type([1, "2"], List[int]) is False
        assert TypeChecker.check_type("not a list", List[str]) is False
    
    def test_check_dict_types(self):
        """测试字典类型检查"""
        assert TypeChecker.check_type({"a": 1, "b": 2}, Dict[str, int]) is True
        assert TypeChecker.check_type({}, Dict[str, int]) is True
        
        assert TypeChecker.check_type({"a": "1"}, Dict[str, int]) is False
        assert TypeChecker.check_type({1: "a"}, Dict[str, int]) is False
    
    def test_check_union_types(self):
        """测试联合类型检查"""
        assert TypeChecker.check_type("hello", Union[str, int]) is True
        assert TypeChecker.check_type(123, Union[str, int]) is True
        assert TypeChecker.check_type(3.14, Union[str, int]) is False
    
    def test_check_optional_types(self):
        """测试可选类型检查"""
        assert TypeChecker.check_type("hello", Optional[str]) is True
        assert TypeChecker.check_type(None, Optional[str]) is True
        assert TypeChecker.check_type(123, Optional[str]) is False
    
    def test_validate_function_signature(self):
        """测试函数签名验证"""
        def test_func(x: int, y: str) -> str:
            return f"{x}:{y}"
        
        assert TypeChecker.validate_function_signature(test_func, 1, "hello") is True
        assert TypeChecker.validate_function_signature(test_func, "1", "hello") is False
        assert TypeChecker.validate_function_signature(test_func, 1, 2) is False


class TestTypeCheckedDecorator:
    """测试类型检查装饰器"""
    
    def test_type_checked_success(self):
        """测试类型检查装饰器成功"""
        @type_checked
        def add_numbers(x: int, y: int) -> int:
            return x + y
        
        result = add_numbers(1, 2)
        assert result == 3
    
    def test_type_checked_parameter_error(self):
        """测试类型检查装饰器参数错误"""
        @type_checked
        def add_numbers(x: int, y: int) -> int:
            return x + y
        
        with pytest.raises(TypeError, match="Type check failed"):
            add_numbers("1", 2)
    
    def test_type_checked_return_error(self):
        """测试类型检查装饰器返回值错误"""
        @type_checked
        def get_string() -> str:
            return 123  # 返回错误类型
        
        with pytest.raises(TypeError, match="Return type check failed"):
            get_string()


class TestDataConverter:
    """测试数据转换器"""
    
    def test_to_camel_case(self):
        """测试下划线转驼峰"""
        assert DataConverter.to_camel_case("user_name") == "userName"
        assert DataConverter.to_camel_case("first_name") == "firstName"
        assert DataConverter.to_camel_case("api_key") == "apiKey"
        assert DataConverter.to_camel_case("simple") == "simple"
    
    def test_to_snake_case(self):
        """测试驼峰转下划线"""
        assert DataConverter.to_snake_case("userName") == "user_name"
        assert DataConverter.to_snake_case("firstName") == "first_name"
        assert DataConverter.to_snake_case("APIKey") == "api_key"
        assert DataConverter.to_snake_case("simple") == "simple"
    
    def test_dict_to_camel_case(self):
        """测试字典键名转驼峰"""
        input_dict = {
            "user_name": "john",
            "first_name": "John",
            "last_name": "Doe",
            "user_info": {
                "phone_number": "123456789",
                "email_address": "john@example.com"
            }
        }
        
        result = DataConverter.dict_to_camel_case(input_dict)
        
        assert "userName" in result
        assert "firstName" in result
        assert "lastName" in result
        assert "userInfo" in result
        assert "phoneNumber" in result["userInfo"]
        assert "emailAddress" in result["userInfo"]
    
    def test_dict_to_snake_case(self):
        """测试字典键名转下划线"""
        input_dict = {
            "userName": "john",
            "firstName": "John",
            "lastName": "Doe",
            "userInfo": {
                "phoneNumber": "123456789",
                "emailAddress": "john@example.com"
            }
        }
        
        result = DataConverter.dict_to_snake_case(input_dict)
        
        assert "user_name" in result
        assert "first_name" in result
        assert "last_name" in result
        assert "user_info" in result
        assert "phone_number" in result["user_info"]
        assert "email_address" in result["user_info"]
    
    def test_dict_conversion_with_lists(self):
        """测试包含列表的字典转换"""
        input_dict = {
            "user_list": [
                {"user_name": "john", "user_age": 30},
                {"user_name": "jane", "user_age": 25}
            ]
        }
        
        result = DataConverter.dict_to_camel_case(input_dict)
        
        assert "userList" in result
        assert result["userList"][0]["userName"] == "john"
        assert result["userList"][1]["userName"] == "jane"


class TestTypedConfig:
    """测试类型安全配置类"""
    
    def test_typed_config_basic(self):
        """测试基础类型安全配置"""
        class TestConfig(TypedConfig):
            name: str
            count: int
            active: bool = True
        
        config = TestConfig(name="test", count=5)
        
        assert config.name == "test"
        assert config.count == 5
        assert config.active is True
    
    def test_typed_config_validation(self):
        """测试类型安全配置验证"""
        class TestConfig(TypedConfig):
            name: str
            count: int
        
        # 正确的类型
        config = TestConfig(name="test", count=5)
        assert config.name == "test"
        
        # 错误的类型应该抛出异常
        with pytest.raises(ValueError):
            TestConfig(name="test", count="not_a_number")
    
    def test_typed_config_dict_conversion(self):
        """测试类型安全配置字典转换"""
        class TestConfig(TypedConfig):
            user_name: str
            user_age: int
        
        config = TestConfig(user_name="john", user_age=30)
        
        # 普通字典
        dict_result = config.dict()
        assert "user_name" in dict_result
        assert dict_result["user_name"] == "john"
        
        # 驼峰命名字典
        camel_result = config.dict(by_alias=True)
        assert "userName" in camel_result
        assert camel_result["userName"] == "john"
    
    def test_typed_config_json_encoders(self):
        """测试类型安全配置 JSON 编码器"""
        class TestConfig(TypedConfig):
            name: str
            created_at: datetime
            user_id: uuid.UUID
            birth_date: date
        
        now = datetime.now()
        test_uuid = uuid.uuid4()
        today = date.today()
        
        config = TestConfig(
            name="test",
            created_at=now,
            user_id=test_uuid,
            birth_date=today
        )
        
        dict_result = config.dict()
        
        # 检查 JSON 编码器是否正常工作
        assert isinstance(dict_result["created_at"], str)
        assert isinstance(dict_result["user_id"], str)
        assert isinstance(dict_result["birth_date"], str)
        
        # 检查格式
        assert dict_result["created_at"].endswith("Z")
        assert dict_result["user_id"] == str(test_uuid)
        assert dict_result["birth_date"] == today.isoformat()