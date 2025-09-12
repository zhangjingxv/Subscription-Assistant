"""
类型定义和类型安全工具
提供完整的类型注解和运行时类型检查
"""

from typing import (
    TypeVar, Generic, Optional, Union, Dict, List, Any, 
    Callable, Awaitable, Protocol, runtime_checkable,
    Literal, get_type_hints, get_origin, get_args
)
from typing_extensions import TypedDict, NotRequired
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime, date
from enum import Enum
import uuid
from dataclasses import dataclass
import inspect


# 基础类型别名
UserID = str
ItemID = str
SourceID = str
CollectionID = str
RequestID = str

# 泛型类型变量
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=BaseModel)


# 枚举类型
class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ContentType(str, Enum):
    """内容类型枚举"""
    ARTICLE = "article"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"


class SourceType(str, Enum):
    """信息源类型枚举"""
    RSS = "rss"
    API = "api"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    SCRAPING = "scraping"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# TypedDict 定义
class DatabaseConfig(TypedDict):
    """数据库配置类型"""
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    echo: NotRequired[bool]


class RedisConfig(TypedDict):
    """Redis 配置类型"""
    url: str
    max_connections: int
    retry_on_timeout: bool
    socket_keepalive: bool


class AIConfig(TypedDict):
    """AI 服务配置类型"""
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    default_model: str
    max_tokens: int
    temperature: float


class MetricsData(TypedDict):
    """指标数据类型"""
    name: str
    value: float
    labels: NotRequired[Dict[str, str]]
    timestamp: NotRequired[datetime]


class HealthCheckResult(TypedDict):
    """健康检查结果类型"""
    status: Literal["healthy", "unhealthy", "degraded"]
    component: str
    message: Optional[str]
    details: NotRequired[Dict[str, Any]]
    response_time: NotRequired[float]


# 协议定义
@runtime_checkable
class Cacheable(Protocol):
    """可缓存协议"""
    
    def cache_key(self) -> str:
        """生成缓存键"""
        ...
    
    def cache_ttl(self) -> int:
        """缓存过期时间（秒）"""
        ...


@runtime_checkable
class Serializable(Protocol):
    """可序列化协议"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """从字典创建实例"""
        ...


@runtime_checkable
class Validatable(Protocol):
    """可验证协议"""
    
    def validate(self) -> bool:
        """验证数据有效性"""
        ...
    
    def validation_errors(self) -> List[str]:
        """获取验证错误"""
        ...


# 数据类定义
@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PaginationParams:
    """分页参数数据类"""
    page: int = Field(ge=1, default=1)
    size: int = Field(ge=1, le=100, default=20)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


@dataclass
class SortParams:
    """排序参数数据类"""
    field: str
    direction: Literal["asc", "desc"] = "desc"
    
    @validator('field')
    def validate_field(cls, v):
        # 这里可以添加字段名验证逻辑
        return v


# 响应类型定义
class APIResponse(BaseModel, Generic[T]):
    """通用 API 响应类型"""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应类型"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @root_validator
    def calculate_pagination_info(cls, values):
        total = values.get('total', 0)
        page = values.get('page', 1)
        size = values.get('size', 20)
        
        pages = (total + size - 1) // size if total > 0 else 0
        has_next = page < pages
        has_prev = page > 1
        
        values.update({
            'pages': pages,
            'has_next': has_next,
            'has_prev': has_prev
        })
        
        return values


class ErrorResponse(BaseModel):
    """错误响应类型"""
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


# 函数类型定义
AsyncHandler = Callable[..., Awaitable[Any]]
SyncHandler = Callable[..., Any]
Handler = Union[AsyncHandler, SyncHandler]

EventHandler = Callable[[str, Dict[str, Any]], Awaitable[None]]
MiddlewareHandler = Callable[[Any, Callable], Awaitable[Any]]


# 类型检查工具
class TypeChecker:
    """运行时类型检查工具"""
    
    @staticmethod
    def check_type(value: Any, expected_type: type) -> bool:
        """检查值是否符合期望类型"""
        try:
            if hasattr(expected_type, '__origin__'):
                # 处理泛型类型
                origin = get_origin(expected_type)
                args = get_args(expected_type)
                
                if origin is Union:
                    return any(TypeChecker.check_type(value, arg) for arg in args)
                elif origin is list:
                    return isinstance(value, list) and all(
                        TypeChecker.check_type(item, args[0]) for item in value
                    ) if args else isinstance(value, list)
                elif origin is dict:
                    if not isinstance(value, dict):
                        return False
                    if len(args) == 2:
                        return all(
                            TypeChecker.check_type(k, args[0]) and 
                            TypeChecker.check_type(v, args[1])
                            for k, v in value.items()
                        )
                    return True
                else:
                    return isinstance(value, origin)
            else:
                return isinstance(value, expected_type)
        except Exception:
            return False
    
    @staticmethod
    def validate_function_signature(func: Callable, *args, **kwargs) -> bool:
        """验证函数调用签名"""
        try:
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # 获取类型注解
            hints = get_type_hints(func)
            
            # 检查参数类型
            for param_name, param_value in bound.arguments.items():
                if param_name in hints:
                    expected_type = hints[param_name]
                    if not TypeChecker.check_type(param_value, expected_type):
                        return False
            
            return True
        except Exception:
            return False


# 类型安全装饰器
def type_checked(func: Callable) -> Callable:
    """类型检查装饰器"""
    
    def wrapper(*args, **kwargs):
        # 检查参数类型
        if not TypeChecker.validate_function_signature(func, *args, **kwargs):
            raise TypeError(f"Type check failed for function {func.__name__}")
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 检查返回值类型
        hints = get_type_hints(func)
        if 'return' in hints:
            return_type = hints['return']
            if not TypeChecker.check_type(result, return_type):
                raise TypeError(f"Return type check failed for function {func.__name__}")
        
        return result
    
    return wrapper


# 数据转换工具
class DataConverter:
    """数据类型转换工具"""
    
    @staticmethod
    def to_camel_case(snake_str: str) -> str:
        """下划线转驼峰"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    @staticmethod
    def to_snake_case(camel_str: str) -> str:
        """驼峰转下划线"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def dict_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
        """字典键名转驼峰"""
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            camel_key = DataConverter.to_camel_case(key)
            if isinstance(value, dict):
                result[camel_key] = DataConverter.dict_to_camel_case(value)
            elif isinstance(value, list):
                result[camel_key] = [
                    DataConverter.dict_to_camel_case(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[camel_key] = value
        
        return result
    
    @staticmethod
    def dict_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
        """字典键名转下划线"""
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            snake_key = DataConverter.to_snake_case(key)
            if isinstance(value, dict):
                result[snake_key] = DataConverter.dict_to_snake_case(value)
            elif isinstance(value, list):
                result[snake_key] = [
                    DataConverter.dict_to_snake_case(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[snake_key] = value
        
        return result


# 类型安全的配置类
class TypedConfig(BaseModel):
    """类型安全的配置基类"""
    
    class Config:
        # 验证赋值
        validate_assignment = True
        # 使用枚举值
        use_enum_values = True
        # 允许额外字段
        extra = "forbid"
        # JSON 编码器
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            date: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """转换为字典，支持驼峰命名"""
        data = super().dict(**kwargs)
        if kwargs.get('by_alias', False):
            return DataConverter.dict_to_camel_case(data)
        return data


# 导出的类型列表
__all__ = [
    # 基础类型
    'UserID', 'ItemID', 'SourceID', 'CollectionID', 'RequestID',
    
    # 枚举类型
    'Environment', 'ContentType', 'SourceType', 'TaskStatus', 
    'UserRole', 'LogLevel',
    
    # TypedDict
    'DatabaseConfig', 'RedisConfig', 'AIConfig', 'MetricsData', 
    'HealthCheckResult',
    
    # 协议
    'Cacheable', 'Serializable', 'Validatable',
    
    # 数据类
    'ProcessingResult', 'PaginationParams', 'SortParams',
    
    # 响应类型
    'APIResponse', 'PaginatedResponse', 'ErrorResponse',
    
    # 函数类型
    'AsyncHandler', 'SyncHandler', 'Handler', 'EventHandler', 
    'MiddlewareHandler',
    
    # 工具类
    'TypeChecker', 'DataConverter', 'TypedConfig',
    
    # 装饰器
    'type_checked'
]