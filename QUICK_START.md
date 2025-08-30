# 🚀 AttentionSync 快速启动指南

恭喜！AttentionSync 的核心代码已经实现完成。现在您可以运行这个智能信息聚合平台了。

## 📋 前置要求

确保您的系统已安装：
- Docker 和 Docker Compose
- Python 3.11+ (用于数据库初始化)
- Node.js 18+ (如果要本地开发前端)

## ⚡ 一键启动

```bash
# 克隆或确保在项目目录中
cd attentionsync

# 运行快速启动脚本
./scripts/start.sh
```

## 🔧 手动启动步骤

如果您希望手动控制启动过程：

### 1. 环境配置

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑配置文件，添加API密钥
nano .env
```

**必需配置**：
- `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` - 用于AI摘要功能

### 2. 启动基础服务

```bash
# 启动数据库、Redis和对象存储
docker-compose up -d postgres redis minio

# 等待服务启动
sleep 10
```

### 3. 初始化数据库

```bash
# 进入API目录并初始化数据库
cd api
python ../scripts/init_db.py
cd ..
```

### 4. 启动应用服务

```bash
# 启动API、Worker和Web服务
docker-compose up -d api worker web
```

## 🌐 访问应用

启动完成后，您可以访问：

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **MinIO控制台**: http://localhost:9001 (minioadmin/minioadmin)

## 👤 默认账号

系统会自动创建一个管理员账号：
- **邮箱**: admin@attentionsync.io
- **密码**: admin123

## 🎯 开始使用

1. **登录系统** - 使用默认账号登录
2. **添加信息源** - 在"订阅"页面添加RSS源或网页
3. **等待采集** - 系统会自动采集和处理内容
4. **查看日读** - 在首页查看AI生成的每日精选

## 📊 系统监控

```bash
# 查看所有服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f worker
```

## 🛠️ 开发模式

如果您想进行开发：

### 后端开发

```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd web
npm install
npm run dev
```

### Worker开发

```bash
cd worker
pip install -r requirements.txt

# 启动Celery worker
celery -A app.celery_app worker --loglevel=info

# 启动Celery beat (另一个终端)
celery -A app.celery_app beat --loglevel=info
```

## 🔄 常用命令

```bash
# 重启所有服务
docker-compose restart

# 重新构建并启动
docker-compose up --build -d

# 停止所有服务
docker-compose down

# 完全清理（包括数据）
docker-compose down -v
```

## 🐛 故障排除

### 数据库连接失败
```bash
# 检查PostgreSQL是否正常启动
docker-compose logs postgres

# 重启数据库服务
docker-compose restart postgres
```

### API服务无法启动
```bash
# 检查API日志
docker-compose logs api

# 确保数据库已初始化
cd api && python ../scripts/init_db.py
```

### 前端页面空白
```bash
# 检查Web服务日志
docker-compose logs web

# 确保API服务正常
curl http://localhost:8000/health
```

## 📚 下一步

1. **配置AI服务** - 添加Claude或OpenAI API密钥以启用摘要功能
2. **添加信息源** - 添加您关注的RSS源、网页或社交媒体
3. **个性化设置** - 通过使用让系统学习您的偏好
4. **探索功能** - 尝试搜索、收藏、分享等功能

## 🤝 需要帮助？

- 查看 [完整文档](docs/)
- 提交 [GitHub Issues](https://github.com/attentionsync/attentionsync/issues)
- 加入 [Discord社区](https://discord.gg/attentionsync)

---

🎉 **恭喜！您现在拥有了一个完全可运行的智能信息聚合平台！**