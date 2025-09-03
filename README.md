# AttentionSync

> 一个遵循Unix哲学的极简RSS阅读器 - "做一件事，并做好"

## 🎯 核心功能

**AttentionSync** 是一个简洁的信息聚合工具，帮助你在3分钟内掌握每日关键信息。

- ✅ **RSS采集** - 自动采集多个信息源
- ✅ **内容聚合** - 统一管理所有订阅内容  
- ✅ **智能去重** - 避免重复信息干扰
- 🔄 **AI摘要** - 可选的智能内容摘要（开发中）

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/attentionsync.git
cd attentionsync

# 运行一键启动脚本（3分钟内完成）
./INSTANT_START.sh
```

脚本会自动完成：
- 环境检查与依赖安装
- 数据库初始化
- 创建测试账号（test@example.com / test123）
- 启动API服务（http://localhost:8000）

### 手动安装

```bash
# 1. 安装依赖
pip install fastapi uvicorn sqlalchemy feedparser

# 2. 启动服务
python start_simple.py

# 3. 访问API文档
open http://localhost:8000/docs
```

## 📦 技术栈

- **后端**: FastAPI + SQLAlchemy
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **任务队列**: Celery + Redis
- **前端**: Next.js + Tailwind CSS

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
└── INSTANT_START.sh   # 一键启动脚本
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

## 🐳 Docker部署

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

MIT License

## 🔗 相关链接

- [API文档](http://localhost:8000/docs)
- [快速开始指南](./QUICK_START.md)
- [部署文档](./DEPLOYMENT.md)

---

> "Simplicity is the ultimate sophistication." - Leonardo da Vinci