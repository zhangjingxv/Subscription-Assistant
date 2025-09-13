# AttentionSync

> 一个遵循Unix哲学的极简RSS阅读器 - "做一件事，并做好"

## 🎯 项目本质

**AttentionSync** 是一个简洁的信息聚合工具，帮助你在3分钟内掌握每日关键信息。

### 核心功能
- ✅ **RSS采集** - 自动采集多个信息源
- ✅ **内容聚合** - 统一管理所有订阅内容  
- ✅ **智能去重** - 避免重复信息干扰
- 🔄 **AI摘要** - 可选的智能内容摘要（开发中）

## 🚀 快速启动

### 一键启动（推荐）
```bash
# 克隆项目
git clone https://github.com/yourusername/attentionsync.git
cd attentionsync

# 运行一键启动脚本（3分钟内完成）
./start_simple.sh
```

脚本会自动完成：
- 环境检查与依赖安装
- 数据库初始化
- 创建测试账号（test@example.com / test123）
- 启动API服务（http://localhost:8000）

### 手动启动
```bash
# 1. 安装依赖
pip install fastapi uvicorn sqlalchemy feedparser pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-dotenv httpx

# 2. 启动服务
cd api
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 3. 访问API文档
open http://localhost:8000/docs
```

## 📦 技术栈

- **后端**: FastAPI + SQLAlchemy
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **前端**: Next.js + Tailwind CSS
- **任务队列**: Celery + Redis

## 🏗️ 项目结构

```
attentionsync/
├── api/                # FastAPI后端
│   ├── app/
│   │   ├── main.py    # 应用入口
│   │   ├── models/    # 数据模型
│   │   ├── routers/   # API路由
│   │   └── core/      # 核心功能
│   └── requirements.txt
├── web/               # Next.js前端
├── worker/            # Celery任务
├── docker-compose.yml # Docker编排
└── start_simple.sh    # 一键启动脚本
```

## 🔧 核心API

```bash
# 健康检查
GET /health

# 用户认证
POST /api/v1/auth/register
POST /api/v1/auth/login

# RSS源管理
GET  /api/v1/sources
POST /api/v1/sources

# 内容获取
GET  /api/v1/items
```

## 📊 当前状态

### ✅ 已完成
- [x] 基础API架构搭建
- [x] 用户认证系统
- [x] RSS源管理
- [x] 内容获取和存储
- [x] 数据库模型设计
- [x] 一键启动脚本
- [x] API文档自动生成

### 🔄 进行中
- [ ] 前端界面开发
- [ ] AI摘要功能
- [ ] 内容去重算法优化
- [ ] 实时更新机制

### 📋 下一步计划

#### 短期（1-2周）
1. **前端界面** - 完成基础UI，让用户能看到内容
2. **内容去重** - 实现智能去重算法
3. **搜索功能** - 基础搜索和过滤
4. **移动端适配** - 响应式设计

#### 中期（1个月）
1. **AI摘要** - 集成AI服务，自动生成内容摘要
2. **实时更新** - WebSocket实时推送新内容
3. **个性化推荐** - 基于用户行为的智能推荐
4. **性能优化** - 缓存、索引、并发优化

#### 长期（3个月）
1. **多语言支持** - 国际化
2. **插件系统** - 支持自定义数据源
3. **团队协作** - 共享订阅和协作功能
4. **高级分析** - 内容趋势分析和洞察

## 🎯 设计哲学

遵循Linus Torvalds的核心原则：

1. **"好品味"** - 消除边界情况，让特殊情况变成正常情况
2. **"永不破坏用户空间"** - 向后兼容，稳定可靠
3. **实用主义** - 解决实际问题，不是假想的威胁
4. **简洁执念** - 做一件事，并做好

## 🔒 安全特性

- JWT认证机制
- 密码加密存储
- SQL注入防护
- XSS防护
- CORS配置

## 📝 环境配置

创建 `.env` 文件：

```env
# 基础配置
ENVIRONMENT=development
DATABASE_URL=sqlite:///./attentionsync.db
SECRET_KEY=your-secret-key-here

# 可选配置
REDIS_URL=redis://localhost:6379
```

## 🐳 Docker部署

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

MIT License

## 🔗 相关链接

- [API文档](http://localhost:8000/docs)
- [项目主页](https://github.com/yourusername/attentionsync)

---

> "Simplicity is the ultimate sophistication." - Leonardo da Vinci

**最后更新**: 2025-01-13  
**当前版本**: 1.0.0  
**维护者**: AttentionSync Team