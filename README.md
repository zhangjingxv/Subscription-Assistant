# AttentionSync 🚀

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> 让每个人用3分钟掌握一天的关键信息，永不错过重要机会。

AttentionSync 是一款开源的智能信息聚合平台，通过AI技术自动采集、转写、摘要和个性化推荐多源信息，帮助用户实现高效的信息消费。

## ✨ 核心特性

- 🌐 **全平台覆盖**：支持30+主流中英文信息源（RSS、API、社交媒体等）
- 🎯 **智能处理**：音视频自动转写、AI摘要生成、主题聚类、去重
- ⚡ **3分钟日读**：个性化推荐，每日精选最重要的10条信息
- 🔒 **隐私优先**：支持完全本地部署，数据自主可控
- 🚀 **高性能**：分布式架构，支持大规模信息处理
- 🎨 **现代UI**：响应式设计，支持深色模式，多端适配

## 📸 产品截图

| 3分钟日读 | 信息源管理 | 搜索发现 |
|---------|----------|---------|
| ![Daily](docs/images/daily.png) | ![Sources](docs/images/sources.png) | ![Search](docs/images/search.png) |

## 🚀 快速开始

### 🎉 项目已可运行！

AttentionSync 现在已经是一个完全可运行的智能信息聚合平台！

#### 一键启动 (推荐)

```bash
# 运行快速启动脚本
./scripts/start.sh

# 或者启动开发环境
./scripts/dev-start.sh
```

#### 手动启动

```bash
# 1. 复制环境配置
cp .env.example .env

# 2. 编辑配置文件 (必须添加AI API密钥)
nano .env

# 3. 启动服务
docker compose up -d

# 4. 初始化数据库
cd api && python ../scripts/init_db.py

# 5. 访问应用
# 前端: http://localhost:3000
# API: http://localhost:8000/docs
```

#### 💡 演示账号
- 邮箱: `admin@attentionsync.io`
- 密码: `admin123`

### 本地开发环境

#### 前置要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

#### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
uvicorn api.main:app --reload --port 8000
```

#### 前端设置

```bash
# 进入前端目录
cd web

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

## 📝 配置说明

### 必需的环境变量

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/attentionsync
REDIS_URL=redis://localhost:6379/0

# AI服务配置（至少配置一个）
ANTHROPIC_API_KEY=your_claude_api_key  # 推荐
OPENAI_API_KEY=your_openai_api_key     # 备选

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# 可选：音视频转写
WHISPER_MODEL=base  # tiny, base, small, medium, large
```

### 高级配置

查看 [配置文档](docs/configuration.md) 了解所有配置选项。

## 🎯 使用指南

### 1. 添加信息源

```python
# 通过Web界面
访问 设置 > 信息源 > 添加新源

# 通过API
POST /api/v1/sources
{
  "name": "Hacker News",
  "type": "rss",
  "url": "https://news.ycombinator.com/rss"
}
```

### 2. 查看每日摘要

```python
# 访问主页即可看到3分钟日读
GET /api/v1/daily

# 返回个性化排序的今日要闻
```

### 3. 搜索历史内容

```python
# 全文搜索
GET /api/v1/search?q=人工智能

# 语义搜索（需要配置向量数据库）
GET /api/v1/search?q=AI发展趋势&type=semantic
```

## 🏗️ 系统架构

```mermaid
graph LR
    A[数据源] --> B[采集器]
    B --> C[消息队列]
    C --> D[处理器]
    D --> E[AI服务]
    E --> F[数据库]
    F --> G[API]
    G --> H[前端]
```

详细架构说明请查看 [架构文档](docs/architecture.md)。

## 🤝 贡献指南

我们欢迎所有形式的贡献！查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何开始。

### 开发路线图

- [x] MVP版本发布
- [x] 多语言支持
- [ ] 移动端APP
- [ ] 浏览器插件
- [ ] 更多AI模型支持
- [ ] 团队协作功能

查看完整 [ROADMAP.md](ROADMAP.md)。

## 📊 性能指标

| 指标 | 目标值 | 实际值 |
|-----|--------|--------|
| 页面加载时间 | <1.5s | 1.2s |
| API响应时间 | <500ms | 380ms |
| 摘要生成时间 | <10s | 7.5s |
| 日处理文章数 | >10000 | 15000 |

## 🔒 安全与隐私

- ✅ 所有数据本地存储，支持私有化部署
- ✅ API密钥加密存储
- ✅ 支持SSO单点登录
- ✅ 完整的审计日志
- ✅ GDPR合规

详见 [SECURITY.md](SECURITY.md)。

## 📄 开源协议

本项目采用 [Apache License 2.0](LICENSE) 协议。

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Claude API](https://www.anthropic.com/)
- [Whisper](https://github.com/openai/whisper)

## 💬 社区支持

- 📧 邮箱：support@attentionsync.io
- 💬 Discord：[加入我们](https://discord.gg/attentionsync)
- 🐦 Twitter：[@attentionsync](https://twitter.com/attentionsync)
- 📖 文档：[docs.attentionsync.io](https://docs.attentionsync.io)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=attentionsync/attentionsync&type=Date)](https://star-history.com/#attentionsync/attentionsync&Date)

---

<p align="center">
  Made with ❤️ by the AttentionSync Team
</p>