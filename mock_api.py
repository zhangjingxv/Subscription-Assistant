#!/usr/bin/env python3
"""
简单的模拟API服务
让前端能够正常显示内容
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="AttentionSync Mock API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3050", "http://127.0.0.1:3050", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class User(BaseModel):
    id: int
    email: str
    is_active: bool = True

class Source(BaseModel):
    id: int
    name: str
    url: str
    type: str = "rss"
    is_active: bool = True

class Item(BaseModel):
    id: int
    title: str
    content: str
    source: str
    published_at: str
    url: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: User

# 模拟数据
MOCK_SOURCES = [
    Source(id=1, name="Hacker News", url="https://news.ycombinator.com/rss", type="rss"),
    Source(id=2, name="阮一峰的网络日志", url="http://www.ruanyifeng.com/blog/atom.xml", type="rss"),
    Source(id=3, name="36氪", url="https://www.36kr.com/feed", type="rss"),
]

MOCK_ITEMS = [
    Item(
        id=1,
        title="AI技术的最新突破",
        content="人工智能技术在各个领域都取得了重大突破...",
        source="Hacker News",
        published_at="2024-01-15T10:00:00Z",
        url="https://example.com/ai-breakthrough"
    ),
    Item(
        id=2,
        title="前端开发最佳实践",
        content="现代前端开发需要关注性能、可访问性和用户体验...",
        source="阮一峰的网络日志",
        published_at="2024-01-15T09:30:00Z",
        url="https://example.com/frontend-best-practices"
    ),
    Item(
        id=3,
        title="创业公司融资趋势",
        content="2024年创业公司融资环境分析...",
        source="36氪",
        published_at="2024-01-15T08:45:00Z",
        url="https://example.com/startup-funding"
    ),
]

# API路由
@app.get("/")
async def root():
    return {"message": "AttentionSync API 正在运行", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AttentionSync"}

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # 简单的模拟登录
    if request.email == "test@example.com" and request.password == "test123":
        return LoginResponse(
            access_token="mock_access_token_123",
            refresh_token="mock_refresh_token_456",
            user=User(id=1, email=request.email)
        )
    return {"error": "Invalid credentials"}

@app.get("/api/v1/sources")
async def get_sources():
    return MOCK_SOURCES

@app.get("/api/v1/items")
async def get_items():
    return MOCK_ITEMS

@app.get("/api/v1/daily/digest")
async def get_daily_digest():
    return {
        "items": MOCK_ITEMS,
        "summary": "今日精选内容，包含AI技术、前端开发和创业趋势等话题",
        "total_count": len(MOCK_ITEMS)
    }

@app.post("/api/v1/items/{item_id}/feedback")
async def record_feedback(item_id: int, action: str):
    return {"message": f"反馈已记录: {action}", "item_id": item_id}

@app.post("/api/v1/items/{item_id}/share")
async def record_share(item_id: int):
    return {"message": "分享已记录", "item_id": item_id}

if __name__ == "__main__":
    print("🚀 启动 AttentionSync 模拟API服务...")
    print("📍 API地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔗 前端地址: http://localhost:3050")
    
    uvicorn.run(
        "mock_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
