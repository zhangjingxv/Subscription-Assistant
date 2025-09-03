# 🚀 AttentionSync MVP 快速启动指南

## 执行摘要

哥，这是让AttentionSync**立即运行**的最简方案。遵循"先跑起来，再优化"的原则，我为你准备了**3分钟启动方案**。

## 🎯 核心运行逻辑

### 产品本质（一句话）
**AttentionSync = RSS阅读器 + AI摘要**

### 核心机制
```
RSS源 → 定时采集 → 内容存储 → AI处理 → 用户阅读
```

### 最小可行产品（MVP）范围
```
必须有：
✅ RSS采集（核心功能）
✅ 内容展示（基础界面）
✅ 用户登录（基本认证）

可以没有：
❌ AI摘要（后期添加）
❌ 个性化推荐（未来功能）
❌ 多媒体处理（扩展功能）
```

## 🏃 3分钟快速启动

### 方案A：最简单启动（开发模式）

```bash
# 1. 克隆项目（30秒）
git clone <your-repo-url> attentionsync
cd attentionsync

# 2. 安装最小依赖（60秒）
pip install fastapi uvicorn sqlalchemy feedparser

# 3. 直接启动（30秒）
python start_simple.py

# 完成！访问 http://localhost:8000
```

### 方案B：Docker一键启动（生产模式）

```bash
# 1. 创建最小配置文件（30秒）
cat > .env << EOF
ENVIRONMENT=development
DATABASE_URL=postgresql://attentionsync:changeme@localhost:5432/attentionsync
SECRET_KEY=dev-secret-key-$(date +%s)
EOF

# 2. 启动所有服务（120秒）
docker-compose up -d postgres redis api

# 3. 检查状态（30秒）
docker-compose ps
curl http://localhost:8000/health

# 完成！系统已运行
```

## 📋 核心运行流程

### 1. 系统启动流程
```
┌─────────────────────────────────────────┐
│           系统启动顺序                   │
├─────────────────────────────────────────┤
│                                          │
│  1. 数据库启动                          │
│     └─ PostgreSQL/SQLite                │
│           ↓                              │
│  2. 缓存启动                            │
│     └─ Redis（可选）                    │
│           ↓                              │
│  3. API服务启动                         │
│     └─ FastAPI on 8000                  │
│           ↓                              │
│  4. 后台任务（可选）                    │
│     └─ Celery Worker                    │
│           ↓                              │
│  5. 前端界面（可选）                    │
│     └─ Next.js on 3000                  │
│                                          │
└─────────────────────────────────────────┘
```

### 2. 数据流转流程
```
用户添加RSS源
    ↓
系统验证URL有效性
    ↓
创建Source记录
    ↓
触发首次采集
    ↓
解析RSS内容
    ↓
存储为Item记录
    ↓
用户查看内容
```

### 3. API调用流程
```
POST /api/v1/auth/register   # 用户注册
    ↓
POST /api/v1/auth/login      # 用户登录
    ↓
GET  /api/v1/sources         # 查看源列表
    ↓
POST /api/v1/sources         # 添加新源
    ↓
GET  /api/v1/items           # 获取内容
```

## 🔧 运行所需条件

### 最小环境要求
```yaml
必须：
  Python: >=3.8
  内存: >=512MB
  磁盘: >=1GB
  
可选：
  Docker: >=20.10
  PostgreSQL: >=12
  Redis: >=6
```

### 核心依赖（仅8个）
```python
# requirements-minimal.txt
fastapi==0.104.1       # Web框架
uvicorn==0.24.0        # ASGI服务器
sqlalchemy==2.0.23     # ORM
feedparser==6.0.10     # RSS解析
pydantic==2.5.1        # 数据验证
python-jose==3.3.0     # JWT认证
passlib==1.7.4         # 密码加密
python-dotenv==1.0.0   # 环境配置
```

### 环境变量配置
```bash
# .env.minimal - 最小配置
ENVIRONMENT=development
DATABASE_URL=sqlite:///./attentionsync.db  # 使用SQLite无需安装数据库
SECRET_KEY=your-secret-key-here
```

## 🎮 快速测试运行

### 1. 健康检查
```bash
# 检查API是否运行
curl http://localhost:8000/health
# 应返回: {"status": "ok"}
```

### 2. 创建测试用户
```bash
# 注册用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

### 3. 添加RSS源
```bash
# 先登录获取token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=testpass123" \
  | jq -r .access_token)

# 添加RSS源
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacker News",
    "url": "https://news.ycombinator.com/rss",
    "type": "rss"
  }'
```

### 4. 获取内容
```bash
# 查看采集的内容
curl http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer $TOKEN"
```

## 🔄 持续优化路径

### Phase 1: 基础运行（当前）
```
目标：系统能跑起来
- ✅ API服务启动
- ✅ 数据库连接
- ✅ 基本CRUD操作
时间：3分钟
```

### Phase 2: 核心功能（第1周）
```
目标：核心功能可用
- [ ] RSS定时采集
- [ ] 内容去重
- [ ] 基础Web界面
时间：1周
```

### Phase 3: 增值功能（第2-4周）
```
目标：提升用户体验
- [ ] AI摘要生成
- [ ] 内容分类
- [ ] 个性化推荐
时间：2-4周
```

### Phase 4: 生产就绪（第2个月）
```
目标：稳定可靠
- [ ] 性能优化
- [ ] 监控告警
- [ ] 自动备份
时间：1个月
```

## 📊 运行状态检查清单

### 启动前检查
- [ ] Python版本 >= 3.8
- [ ] 端口8000未被占用
- [ ] 有写入权限（SQLite需要）

### 启动后验证
- [ ] API健康检查通过
- [ ] 数据库连接正常
- [ ] 能创建用户
- [ ] 能添加RSS源
- [ ] 能获取内容列表

### 常见问题排查
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 端口被占用 | 8000端口已用 | 修改端口或停止占用进程 |
| 数据库连接失败 | 配置错误 | 检查DATABASE_URL |
| 依赖安装失败 | 版本冲突 | 使用虚拟环境 |
| 权限错误 | 无写入权限 | 确保当前目录可写 |

## 🚦 下一步行动

### 立即执行（5分钟内）
1. **运行最简启动脚本**
   ```bash
   python start_simple.py
   ```

2. **验证系统运行**
   ```bash
   curl http://localhost:8000/health
   ```

3. **添加第一个RSS源**
   - 使用上面的测试命令
   - 或通过API文档界面：http://localhost:8000/docs

### 今日完成（24小时内）
1. **部署基础监控**
   - 添加日志记录
   - 设置错误告警

2. **配置定时任务**
   - 每小时采集RSS
   - 每日清理旧数据

3. **创建简单界面**
   - 登录页面
   - 内容列表页
   - RSS源管理页

### 本周目标（7天内）
1. **完善核心功能**
   - RSS采集稳定运行
   - 内容去重机制
   - 基础搜索功能

2. **添加测试覆盖**
   - 核心API测试
   - RSS解析测试
   - 用户认证测试

3. **准备生产部署**
   - 配置Nginx
   - 设置HTTPS
   - 数据备份策略

## 💡 核心洞察

### MVP的本质
> "MVP不是做一个残缺的产品，而是做一个完整但范围最小的产品。"

你的AttentionSync MVP = **能用的RSS阅读器**，而不是**带AI的半成品**。

### 运行优先原则
1. **能跑 > 跑得快**
2. **简单 > 功能全**
3. **稳定 > 创新**

### 进化路径
```
能跑起来 → 核心功能 → 用户体验 → 性能优化 → 规模扩展
   ↑
  当前位置
```

## 🎯 成功标准

### MVP成功指标
- ✅ 3分钟内启动成功
- ✅ 能添加并采集RSS源
- ✅ 能展示采集的内容
- ✅ 系统稳定运行24小时

### 记住
> "Done is better than perfect. Running is better than planning."
> 
> 完成比完美更重要，运行比计划更重要。

---

**文档版本**: 1.0.0
**创建时间**: 2024-12-29
**最后验证**: 2024-12-29

**作者**: Claude (践行Linus Torvalds的实用主义哲学)

> "这份指南的目标只有一个：让你的项目在3分钟内跑起来。其他的，都是后话。"