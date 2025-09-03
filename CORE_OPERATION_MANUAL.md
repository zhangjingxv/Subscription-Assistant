# 📖 AttentionSync 核心运行手册

## 目标定位

哥，这份手册记录了AttentionSync的**核心运行机制**，确保任何人都能理解并运行这个系统。

## 一、产品核心逻辑

### 1.1 产品定位（三层理解）

#### 现象层：用户看到什么
```
一个RSS阅读器，能自动采集和展示内容
```

#### 本质层：系统做什么
```
信息聚合平台：采集 → 处理 → 分发
```

#### 哲学层：为什么存在
```
解决信息过载问题，让用户3分钟掌握关键信息
```

### 1.2 核心价值链
```
┌────────────────────────────────────────────┐
│            AttentionSync 价值链            │
├────────────────────────────────────────────┤
│                                             │
│  信息源 → 自动采集 → 智能处理 → 个性分发    │
│    ↓         ↓          ↓         ↓        │
│  RSS     定时任务    AI摘要    用户偏好     │
│  API     去重过滤    分类打标   推荐算法     │
│  网页    格式统一    情感分析   时间排序     │
│                                             │
└────────────────────────────────────────────┘
```

### 1.3 系统边界定义

**系统要做的**：
- ✅ 采集公开信息源
- ✅ 统一内容格式
- ✅ 提供阅读界面
- ✅ 基础个性化

**系统不做的**：
- ❌ 创造原创内容
- ❌ 社交互动功能
- ❌ 付费订阅管理
- ❌ 实时通讯

## 二、关键运行流程

### 2.1 系统启动流程

```mermaid
graph TD
    A[开始] --> B[环境检查]
    B --> C{依赖完整?}
    C -->|否| D[安装依赖]
    D --> E[初始化数据库]
    C -->|是| E
    E --> F[启动API服务]
    F --> G[启动后台任务]
    G --> H[系统就绪]
```

#### 详细步骤
```bash
# Step 1: 环境检查
python --version  # 需要 >= 3.8
pip --version     # 需要pip可用

# Step 2: 依赖安装
pip install -r requirements-minimal.txt

# Step 3: 数据库初始化
python -c "from api.app.core.db import init_db; init_db()"

# Step 4: 启动API服务
cd api && uvicorn app.main:app --reload

# Step 5: 启动后台任务（可选）
celery -A app.celery_app worker --loglevel=info
```

### 2.2 用户注册流程

```
用户访问 → 填写邮箱密码 → 系统验证 → 创建账户 → 返回Token
```

#### API调用示例
```python
# 注册请求
POST /api/v1/auth/register
{
    "email": "user@example.com",
    "password": "SecurePass123"
}

# 返回结果
{
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-12-29T10:00:00Z"
}
```

### 2.3 RSS源添加流程

```
用户登录 → 提交RSS URL → 验证URL有效性 → 创建Source记录 → 触发首次采集
```

#### 核心代码逻辑
```python
def add_source(url: str, user_id: int):
    # 1. 验证URL
    if not validate_rss_url(url):
        raise ValueError("Invalid RSS URL")
    
    # 2. 检查重复
    if source_exists(url, user_id):
        raise ValueError("Source already exists")
    
    # 3. 创建记录
    source = Source(
        url=url,
        user_id=user_id,
        status="active"
    )
    db.add(source)
    db.commit()
    
    # 4. 触发采集
    fetch_rss_task.delay(source.id)
    
    return source
```

### 2.4 内容采集流程

```
定时触发 → 获取活跃源 → 并发采集 → 解析内容 → 去重存储 → 通知用户
```

#### 采集任务实现
```python
@celery.task
def fetch_all_sources():
    """每小时执行的采集任务"""
    sources = get_active_sources()
    
    for source in sources:
        fetch_single_source.delay(source.id)

@celery.task
def fetch_single_source(source_id: int):
    """采集单个源"""
    source = get_source(source_id)
    
    try:
        # 1. 获取内容
        content = fetch_rss(source.url)
        
        # 2. 解析条目
        items = parse_rss(content)
        
        # 3. 去重存储
        for item in items:
            if not item_exists(item.guid):
                save_item(item, source_id)
        
        # 4. 更新源状态
        update_source_status(source_id, "success")
        
    except Exception as e:
        update_source_status(source_id, "error", str(e))
```

### 2.5 内容展示流程

```
用户请求 → 认证验证 → 查询过滤 → 分页排序 → 返回数据
```

#### API实现
```python
@router.get("/items")
async def get_items(
    skip: int = 0,
    limit: int = 20,
    source_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """获取内容列表"""
    query = db.query(Item).filter(Item.user_id == current_user.id)
    
    if source_id:
        query = query.filter(Item.source_id == source_id)
    
    items = query.order_by(Item.created_at.desc()) \
                 .offset(skip) \
                 .limit(limit) \
                 .all()
    
    return items
```

## 三、系统运行条件

### 3.1 硬件要求

| 组件 | 最小配置 | 推荐配置 | 说明 |
|------|---------|---------|------|
| CPU | 1核 | 2核+ | 采集任务需要并发 |
| 内存 | 512MB | 2GB+ | 缓存和处理需要 |
| 磁盘 | 1GB | 10GB+ | 存储内容和日志 |
| 网络 | 1Mbps | 10Mbps+ | 采集外部源 |

### 3.2 软件依赖

#### 必需组件
```yaml
运行时:
  Python: ">=3.8,<4.0"
  pip: "最新稳定版"

核心库:
  fastapi: "0.104.1"      # Web框架
  sqlalchemy: "2.0.23"    # ORM
  pydantic: "2.5.1"       # 数据验证
  uvicorn: "0.24.0"       # ASGI服务器
```

#### 可选组件
```yaml
生产部署:
  PostgreSQL: ">=12"       # 生产数据库
  Redis: ">=6"            # 缓存队列
  Nginx: ">=1.18"         # 反向代理
  Docker: ">=20.10"       # 容器化

增强功能:
  Celery: "5.3.4"         # 异步任务
  OpenAI: "1.3.8"         # AI摘要
  Sentry: "1.38.0"        # 错误监控
```

### 3.3 环境配置

#### 开发环境（.env.dev）
```bash
# 基础配置
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG

# 数据库（使用SQLite）
DATABASE_URL=sqlite:///./dev.db

# 安全（开发用密钥）
SECRET_KEY=dev-secret-key
JWT_SECRET=dev-jwt-secret

# API配置
API_HOST=127.0.0.1
API_PORT=8000
```

#### 生产环境（.env.prod）
```bash
# 基础配置
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# 数据库（使用PostgreSQL）
DATABASE_URL=postgresql://user:pass@localhost/dbname

# 安全（强密钥）
SECRET_KEY=${SECURE_RANDOM_KEY}
JWT_SECRET=${SECURE_JWT_KEY}

# API配置
API_HOST=0.0.0.0
API_PORT=8000

# 监控
SENTRY_DSN=${SENTRY_DSN}
```

## 四、关键数据流

### 4.1 数据模型关系
```
User (用户)
  ↓ 1:N
Source (信息源)
  ↓ 1:N
Item (内容条目)
  ↓ 1:N
Summary (AI摘要)
```

### 4.2 数据生命周期
```
创建 → 更新 → 归档 → 删除
 ↓      ↓      ↓      ↓
新增   采集   30天   90天
```

### 4.3 数据流向图
```
外部数据源
    ↓ [HTTP/RSS]
采集服务
    ↓ [解析]
原始数据
    ↓ [清洗]
标准格式
    ↓ [存储]
数据库
    ↓ [查询]
API服务
    ↓ [JSON]
前端展示
```

## 五、运行监控指标

### 5.1 系统健康指标
```python
# 健康检查端点
GET /health
Response: {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "uptime": 3600,
    "version": "1.0.0"
}
```

### 5.2 关键性能指标（KPI）
| 指标 | 目标值 | 告警阈值 | 监控方法 |
|------|--------|---------|----------|
| API响应时间 | <200ms | >1s | Prometheus |
| 采集成功率 | >95% | <90% | 日志分析 |
| 数据库连接数 | <100 | >150 | pg_stat |
| 内存使用率 | <70% | >90% | System |
| 错误率 | <0.1% | >1% | Sentry |

### 5.3 业务运行指标
```sql
-- 每日活跃用户
SELECT COUNT(DISTINCT user_id) 
FROM user_activities 
WHERE created_at > NOW() - INTERVAL '1 day';

-- 源采集情况
SELECT status, COUNT(*) 
FROM sources 
GROUP BY status;

-- 内容增长趋势
SELECT DATE(created_at), COUNT(*) 
FROM items 
GROUP BY DATE(created_at) 
ORDER BY DATE(created_at) DESC 
LIMIT 30;
```

## 六、故障排查手册

### 6.1 常见问题速查

| 症状 | 可能原因 | 排查步骤 | 解决方案 |
|------|---------|---------|----------|
| API无响应 | 服务未启动 | `ps aux \| grep uvicorn` | 重启服务 |
| 数据库连接失败 | 配置错误 | 检查DATABASE_URL | 修正配置 |
| 采集失败 | 网络问题 | `curl RSS_URL` | 检查防火墙 |
| 内存溢出 | 数据量过大 | `top`查看内存 | 增加分页限制 |
| 登录失败 | Token过期 | 检查JWT配置 | 刷新Token |

### 6.2 调试命令集
```bash
# 检查服务状态
systemctl status attentionsync

# 查看实时日志
tail -f /var/log/attentionsync/api.log

# 数据库连接测试
python -c "from api.app.core.db import test_connection; test_connection()"

# API健康检查
curl http://localhost:8000/health

# 清理缓存
redis-cli FLUSHDB

# 重建数据库
alembic upgrade head
```

### 6.3 应急恢复流程
```
1. 评估影响范围
   └─ 确定受影响的服务和用户

2. 快速止损
   └─ 切换到维护模式
   └─ 停止问题服务

3. 问题定位
   └─ 查看错误日志
   └─ 分析监控数据

4. 实施修复
   └─ 应用热修复
   └─ 或回滚到稳定版本

5. 验证恢复
   └─ 运行健康检查
   └─ 小流量测试

6. 全量恢复
   └─ 逐步放开流量
   └─ 持续监控

7. 复盘总结
   └─ 记录问题原因
   └─ 更新应急预案
```

## 七、优化迭代路径

### 7.1 MVP → v1.0 路线图
```
MVP (当前)
├─ 基础RSS采集
├─ 用户认证
└─ 内容展示

v0.2 (1周)
├─ 定时采集
├─ 内容去重
└─ 基础搜索

v0.5 (2周)
├─ AI摘要
├─ 分类标签
└─ 阅读历史

v0.8 (1月)
├─ 个性推荐
├─ 数据分析
└─ 移动适配

v1.0 (2月)
├─ 性能优化
├─ 监控完善
└─ 文档齐全
```

### 7.2 性能优化清单
- [ ] 数据库索引优化
- [ ] API响应缓存
- [ ] 图片懒加载
- [ ] 分页查询优化
- [ ] 异步任务队列
- [ ] CDN静态资源
- [ ] 数据库连接池
- [ ] Redis缓存层

### 7.3 功能增强计划
- [ ] 多语言支持
- [ ] 主题定制
- [ ] 导出功能
- [ ] 批量操作
- [ ] 快捷键支持
- [ ] 离线阅读
- [ ] 社交分享
- [ ] 数据统计

## 八、核心原则总结

### 8.1 设计原则
1. **简单优先** - 能简单解决的不要复杂化
2. **渐进增强** - 先保证基础功能，再添加高级特性
3. **数据驱动** - 基于实际使用数据做决策
4. **用户至上** - 所有功能服务于用户价值

### 8.2 运维原则
1. **监控先行** - 没有监控就没有优化
2. **自动化** - 重复的事情自动化
3. **文档化** - 关键流程必须有文档
4. **可回滚** - 任何变更都要能回滚

### 8.3 进化原则
1. **小步快跑** - 频繁发布小更新
2. **数据验证** - 用数据验证假设
3. **持续重构** - 保持代码健康
4. **学习成长** - 从错误中学习

## 九、关键决策记录

### 9.1 技术选型决策
| 决策点 | 选择 | 理由 | 时间 |
|--------|------|------|------|
| Web框架 | FastAPI | 性能好、类型安全 | 2024.08 |
| 数据库 | PostgreSQL | 成熟稳定、功能全 | 2024.08 |
| 任务队列 | Celery | 生态成熟、文档全 | 2024.08 |
| 前端框架 | Next.js | 全栈方案、SEO友好 | 2024.08 |

### 9.2 架构决策
| 决策 | 原因 | 影响 |
|------|------|------|
| 单体优先 | 降低复杂度 | 易于开发部署 |
| 同步API | 简化实现 | 可能有性能瓶颈 |
| SQLite开发 | 零配置 | 需迁移到PG生产 |

## 十、快速参考

### 10.1 常用命令
```bash
# 启动开发服务器
make dev

# 运行测试
make test

# 构建生产版本
make build

# 部署到生产
make deploy

# 查看日志
make logs

# 数据库迁移
make migrate
```

### 10.2 API快速参考
```
认证相关:
POST   /api/v1/auth/register    # 注册
POST   /api/v1/auth/login       # 登录
POST   /api/v1/auth/refresh     # 刷新Token

源管理:
GET    /api/v1/sources          # 列表
POST   /api/v1/sources          # 添加
PUT    /api/v1/sources/{id}     # 更新
DELETE /api/v1/sources/{id}     # 删除

内容相关:
GET    /api/v1/items            # 列表
GET    /api/v1/items/{id}       # 详情
POST   /api/v1/items/{id}/read  # 标记已读
```

### 10.3 环境变量参考
```bash
# 必需变量
DATABASE_URL      # 数据库连接
SECRET_KEY        # 应用密钥

# 可选变量
REDIS_URL         # Redis连接
SENTRY_DSN        # 错误追踪
API_KEYS          # 第三方API密钥
```

---

**手册版本**: 1.0.0
**创建时间**: 2024-12-29
**适用版本**: AttentionSync v0.1+

**编写原则**: 
- 可追溯：每个流程都有记录
- 可复盘：问题都有解决方案
- 可执行：命令都经过验证

> "This manual is your map. When lost, return here."