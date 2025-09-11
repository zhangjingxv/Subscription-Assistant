"""
优化的数据库配置
包含连接池、查询优化、缓存等功能
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy import event, text, select
from sqlalchemy.engine import Engine
import structlog
import time

from app.core.config import get_settings
from app.core.cache import cache_manager

logger = structlog.get_logger()
settings = get_settings()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.async_session_factory = None
        self.read_engine = None
        self.read_session_factory = None
        self._connection_pool_stats = {
            "active_connections": 0,
            "total_connections": 0,
            "query_count": 0,
            "slow_queries": []
        }
    
    def create_engine(self, database_url: str, is_read_only: bool = False) -> None:
        """创建数据库引擎"""
        
        # 根据环境选择连接池
        if settings.environment == "testing":
            poolclass = NullPool  # 测试环境不使用连接池
            pool_size = 0
            max_overflow = 0
        else:
            poolclass = QueuePool
            pool_size = getattr(settings, 'db_pool_size', 20)
            max_overflow = getattr(settings, 'db_max_overflow', 30)
        
        engine_kwargs = {
            "url": database_url,
            "poolclass": poolclass,
            "echo": settings.environment == "development",
            "future": True,
        }
        
        if poolclass != NullPool:
            engine_kwargs.update({
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": getattr(settings, 'db_pool_timeout', 30),
                "pool_recycle": getattr(settings, 'db_pool_recycle', 3600),
                "pool_pre_ping": True,  # 连接健康检查
            })
        
        engine = create_async_engine(**engine_kwargs)
        
        # 添加事件监听器
        self._setup_event_listeners(engine)
        
        return engine
    
    def _setup_event_listeners(self, engine):
        """设置数据库事件监听器"""
        
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """SQLite 优化设置"""
            if "sqlite" in str(engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=memory")
                cursor.close()
        
        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行前的监听"""
            context._query_start_time = time.time()
            self._connection_pool_stats["query_count"] += 1
        
        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行后的监听"""
            total = time.time() - context._query_start_time
            
            # 记录慢查询
            if total > 1.0:  # 超过1秒的查询
                slow_query = {
                    "statement": statement[:200] + "..." if len(statement) > 200 else statement,
                    "duration": total,
                    "timestamp": time.time()
                }
                self._connection_pool_stats["slow_queries"].append(slow_query)
                
                # 只保留最近50个慢查询
                if len(self._connection_pool_stats["slow_queries"]) > 50:
                    self._connection_pool_stats["slow_queries"].pop(0)
                
                logger.warning(
                    "Slow query detected",
                    duration=total,
                    statement=statement[:100]
                )
    
    async def initialize(self):
        """初始化数据库连接"""
        # 主数据库（读写）
        self.engine = self.create_engine(settings.database_url)
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 读库（如果配置了）
        read_db_url = getattr(settings, 'database_read_url', None)
        if read_db_url and read_db_url != settings.database_url:
            self.read_engine = self.create_engine(read_db_url, is_read_only=True)
            self.read_session_factory = async_sessionmaker(
                self.read_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("Read-only database configured")
        else:
            # 如果没有配置读库，使用主库
            self.read_engine = self.engine
            self.read_session_factory = self.async_session_factory
        
        logger.info("Database connections initialized")
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
        if self.read_engine and self.read_engine != self.engine:
            await self.read_engine.dispose()
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        session_factory = self.read_session_factory if read_only else self.async_session_factory
        
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        stats = self._connection_pool_stats.copy()
        
        if self.engine and hasattr(self.engine.pool, 'size'):
            stats.update({
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "invalid": self.engine.pool.invalid()
            })
        
        return stats


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_user_sources_query():
        """优化用户信息源查询"""
        from app.models.source import Source
        from app.models.item import Item
        
        # 预加载关联数据，避免 N+1 查询
        return select(Source).options(
            selectinload(Source.items.and_(
                Item.created_at >= text("CURRENT_DATE - INTERVAL '7 days'")
            ))
        )
    
    @staticmethod
    def optimize_user_items_query():
        """优化用户内容项查询"""
        from app.models.item import Item
        from app.models.source import Source
        
        return select(Item).options(
            joinedload(Item.source)
        ).order_by(Item.created_at.desc())
    
    @staticmethod
    async def get_user_stats_optimized(db: AsyncSession, user_id: str) -> Dict[str, int]:
        """优化的用户统计查询"""
        cache_key = f"user_stats:{user_id}"
        cached_stats = await cache_manager.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # 单个查询获取所有统计信息
        from app.models.source import Source, SourceStatus
        from app.models.item import Item
        
        query = text("""
            SELECT 
                COUNT(DISTINCT s.id) as total_sources,
                COUNT(DISTINCT CASE WHEN s.status = :active_status THEN s.id END) as active_sources,
                COUNT(DISTINCT CASE WHEN s.status = :paused_status THEN s.id END) as paused_sources,
                COUNT(DISTINCT CASE WHEN s.status = :error_status THEN s.id END) as error_sources,
                COUNT(DISTINCT i.id) as total_items,
                COUNT(DISTINCT CASE WHEN i.created_at >= CURRENT_DATE THEN i.id END) as today_items
            FROM sources s
            LEFT JOIN items i ON s.id = i.source_id
            WHERE s.user_id = :user_id
        """)
        
        result = await db.execute(query, {
            "user_id": user_id,
            "active_status": SourceStatus.ACTIVE.value,
            "paused_status": SourceStatus.PAUSED.value,
            "error_status": SourceStatus.ERROR.value
        })
        
        row = result.fetchone()
        stats = {
            "total_sources": row.total_sources or 0,
            "active_sources": row.active_sources or 0,
            "paused_sources": row.paused_sources or 0,
            "error_sources": row.error_sources or 0,
            "total_items": row.total_items or 0,
            "today_items": row.today_items or 0
        }
        
        # 缓存5分钟
        await cache_manager.set(cache_key, stats, ttl=300)
        return stats


class DatabaseHealthChecker:
    """数据库健康检查"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def check_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "message": "Database connection is working",
                    "timestamp": time.time()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def check_read_replica(self) -> Dict[str, Any]:
        """检查读库连接"""
        if self.db_manager.read_engine == self.db_manager.engine:
            return {"status": "not_configured", "message": "Read replica not configured"}
        
        try:
            async with self.db_manager.get_session(read_only=True) as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "message": "Read replica connection is working",
                    "timestamp": time.time()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Read replica connection failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        stats = self.db_manager.get_stats()
        
        # 添加慢查询分析
        slow_queries = stats.get("slow_queries", [])
        avg_slow_query_time = 0
        if slow_queries:
            avg_slow_query_time = sum(q["duration"] for q in slow_queries) / len(slow_queries)
        
        return {
            "connection_pool": {
                "pool_size": stats.get("pool_size", 0),
                "checked_out": stats.get("checked_out", 0),
                "overflow": stats.get("overflow", 0)
            },
            "query_performance": {
                "total_queries": stats.get("query_count", 0),
                "slow_queries_count": len(slow_queries),
                "avg_slow_query_time": avg_slow_query_time
            },
            "timestamp": time.time()
        }


# 全局数据库管理器
db_manager = DatabaseManager()
query_optimizer = QueryOptimizer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（写操作）"""
    async with db_manager.get_session(read_only=False) as session:
        yield session


async def get_db_read() -> AsyncGenerator[AsyncSession, None]:
    """获取只读数据库会话"""
    async with db_manager.get_session(read_only=True) as session:
        yield session


async def init_db():
    """初始化数据库"""
    await db_manager.initialize()


async def close_db():
    """关闭数据库连接"""
    await db_manager.close()


# 数据库健康检查
health_checker = DatabaseHealthChecker(db_manager)


async def database_health_check() -> Dict[str, Any]:
    """数据库健康检查端点"""
    main_db = await health_checker.check_connection()
    read_db = await health_checker.check_read_replica()
    performance = await health_checker.get_performance_metrics()
    
    overall_status = "healthy"
    if main_db["status"] != "healthy":
        overall_status = "unhealthy"
    elif read_db["status"] == "unhealthy":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "main_database": main_db,
        "read_replica": read_db,
        "performance_metrics": performance,
        "timestamp": time.time()
    }