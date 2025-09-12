"""
pytest 配置文件
提供测试夹具和公共测试工具
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis

# 设置测试环境
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # 使用测试数据库

from app.main import create_app
from app.core.db import get_db, Base
from app.core.config import get_settings
from app.models.user import User
from app.models.source import Source
from app.models.item import Item


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    """获取测试设置"""
    return get_settings()


@pytest.fixture(scope="function")
def db_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    yield engine
    
    # 清理
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def app(db_session):
    """创建测试应用"""
    app = create_app()
    
    # 重写数据库依赖
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # 清理
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def redis_client():
    """创建 Redis 测试客户端"""
    client = redis.from_url("redis://localhost:6379/15", decode_responses=True)
    
    # 清理测试数据库
    await client.flushdb()
    
    yield client
    
    # 清理
    await client.flushdb()
    await client.close()


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis 客户端"""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.ping.return_value = True
    return mock


@pytest.fixture(scope="function")
def sample_user_data():
    """示例用户数据"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture(scope="function")
def sample_user(db_session, sample_user_data):
    """创建示例用户"""
    from app.utils.security import get_password_hash
    
    user = User(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        password_hash=get_password_hash(sample_user_data["password"]),
        full_name=sample_user_data["full_name"],
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def sample_source_data():
    """示例信息源数据"""
    return {
        "name": "Test RSS Feed",
        "type": "rss",
        "platform": "generic",
        "url": "https://example.com/feed.xml",
        "is_active": True
    }


@pytest.fixture(scope="function")
def sample_source(db_session, sample_user, sample_source_data):
    """创建示例信息源"""
    source = Source(
        user_id=sample_user.id,
        **sample_source_data
    )
    
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    
    return source


@pytest.fixture(scope="function")
def sample_item_data():
    """示例内容项数据"""
    return {
        "title": "Test Article",
        "url": "https://example.com/article",
        "content_type": "article",
        "raw_content": "This is a test article content.",
        "author": "Test Author"
    }


@pytest.fixture(scope="function")
def sample_item(db_session, sample_source, sample_item_data):
    """创建示例内容项"""
    item = Item(
        source_id=sample_source.id,
        **sample_item_data
    )
    
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    
    return item


@pytest.fixture(scope="function")
def auth_headers(sample_user):
    """生成认证头"""
    from app.utils.security import create_access_token
    
    token = create_access_token(data={"sub": sample_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def mock_openai():
    """Mock OpenAI 客户端"""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="This is a test summary."
                )
            )
        ],
        usage=MagicMock(
            total_tokens=100
        )
    )
    return mock


@pytest.fixture(scope="function")
def mock_anthropic():
    """Mock Anthropic 客户端"""
    mock = MagicMock()
    mock.messages.create.return_value = MagicMock(
        content=[
            MagicMock(
                text="This is a test summary from Claude."
            )
        ],
        usage=MagicMock(
            input_tokens=50,
            output_tokens=50
        )
    )
    return mock


@pytest.fixture(scope="function")
def mock_feedparser():
    """Mock feedparser"""
    mock = MagicMock()
    mock.parse.return_value = MagicMock(
        entries=[
            {
                "title": "Test Entry 1",
                "link": "https://example.com/entry1",
                "description": "Test description 1",
                "published": "Mon, 01 Jan 2024 12:00:00 GMT"
            },
            {
                "title": "Test Entry 2", 
                "link": "https://example.com/entry2",
                "description": "Test description 2",
                "published": "Mon, 01 Jan 2024 13:00:00 GMT"
            }
        ],
        feed=MagicMock(
            title="Test Feed",
            description="Test feed description"
        )
    )
    return mock


@pytest.fixture(scope="function")
def mock_celery_task():
    """Mock Celery 任务"""
    mock = MagicMock()
    mock.delay.return_value = MagicMock(
        id="test-task-id",
        state="SUCCESS",
        result={"status": "completed"}
    )
    return mock


@pytest.fixture(autouse=True)
def clean_env():
    """清理环境变量"""
    # 保存原始环境变量
    original_env = os.environ.copy()
    
    yield
    
    # 恢复环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def temp_file():
    """创建临时文件"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    
    # 清理
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def temp_dir():
    """创建临时目录"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    yield temp_dir
    
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


# 测试工具函数
def assert_response_success(response, expected_status=200):
    """断言响应成功"""
    assert response.status_code == expected_status
    data = response.json()
    assert data.get("success", True) is True


def assert_response_error(response, expected_status=400, expected_code=None):
    """断言响应错误"""
    assert response.status_code == expected_status
    data = response.json()
    assert "error" in data
    
    if expected_code:
        assert data["error"]["code"] == expected_code


def create_test_data(db_session, model_class, count=5, **kwargs):
    """批量创建测试数据"""
    items = []
    for i in range(count):
        item_data = {**kwargs}
        # 为字符串字段添加索引
        for key, value in item_data.items():
            if isinstance(value, str) and not value.endswith(str(i)):
                item_data[key] = f"{value}_{i}"
        
        item = model_class(**item_data)
        db_session.add(item)
        items.append(item)
    
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    
    return items


# 性能测试工具
@pytest.fixture
def benchmark_timer():
    """性能测试计时器"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# 异步测试工具
def async_test(func):
    """异步测试装饰器"""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


# 数据库测试工具
def truncate_tables(db_session, *table_names):
    """清空指定表"""
    for table_name in table_names:
        db_session.execute(f"DELETE FROM {table_name}")
    db_session.commit()


# Mock 工具
class MockResponse:
    """Mock HTTP 响应"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# 测试标记
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.redis = pytest.mark.redis
pytest.mark.database = pytest.mark.database