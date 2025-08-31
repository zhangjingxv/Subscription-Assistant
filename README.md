# AttentionSync 🚀

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Project Status](https://img.shields.io/badge/Status-75%25%20Complete-orange)](https://github.com/zhangjingxv/Subscription-Assistant)

> 让每个人用3分钟掌握一天的关键信息，永不错过重要机会。

AttentionSync 是一款开源的智能信息聚合平台，通过AI技术自动采集、转写、摘要和个性化推荐多源信息，帮助用户实现高效的信息消费。

## ✨ 核心特性

- 🌐 **全平台覆盖**：支持30+主流中英文信息源（RSS、API、社交媒体等）
- 🎯 **智能处理**：音视频自动转写、AI摘要生成、主题聚类、去重
- ⚡ **3分钟日读**：个性化推荐，每日精选最重要的10条信息
- 🔒 **隐私优先**：支持完全本地部署，数据自主可控
- 🚀 **高性能**：分布式架构，支持大规模信息处理
- 🎨 **现代UI**：响应式设计，支持深色模式，多端适配

## 📊 项目状态

**当前完成度: 75%** 🎯

- ✅ **基础架构** (100%) - FastAPI后端、数据库模型、认证系统
- ✅ **核心功能** (80%) - 用户管理、内容采集、AI处理
- 🔄 **前端界面** (50%) - Next.js框架、基础组件
- 🔄 **部署运维** (40%) - Docker化、环境配置

详细状态请查看 [项目状态总结](PROJECT_STATUS_SUMMARY.md)

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
# 1. 克隆项目
git clone https://github.com/zhangjingxv/Subscription-Assistant.git
cd Subscription-Assistant

# 2. 安装Python依赖
cd api
pip install -r requirements.txt

# 3. 启动API服务
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# 4. 访问应用
# API: http://localhost:8001
# 健康检查: http://localhost:8001/health
```

#### 💡 演示账号
- 邮箱: `admin@attentionsync.io`
- 密码: `admin123`

## 🔧 技术架构

### 后端技术栈
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + SQLite (开发)
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis
- **AI服务**: OpenAI, Anthropic Claude

### 前端技术栈
- **框架**: Next.js 14
- **样式**: Tailwind CSS
- **类型**: TypeScript

### 基础设施
- **容器化**: Docker + Docker Compose
- **对象存储**: MinIO
- **任务队列**: Celery

## 📈 开发路线图

### 🎯 短期目标 (1-2个月)
- 完善错误处理和日志记录
- 添加测试覆盖
- 实现Redis缓存层
- 优化数据库性能

### 🔮 中期目标 (3-6个月)
- AI能力增强
- 微服务架构改造
- 搜索引擎集成
- 性能优化

### 🌟 长期目标 (6-12个月)
- 智能化升级
- 平台化发展
- 国际化支持

详细规划请查看 [未来优化方向](FUTURE_OPTIMIZATION.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式
- 🐛 **Bug报告**: 通过 [GitHub Issues](https://github.com/zhangjingxv/Subscription-Assistant/issues)
- 💡 **功能建议**: 提交 Feature Request
- 🔧 **代码贡献**: Fork + Pull Request
- 📚 **文档改进**: 直接编辑或PR

### 开发环境设置
1. Fork 项目
2. 克隆你的Fork: `git clone https://github.com/YOUR_USERNAME/Subscription-Assistant.git`
3. 创建功能分支: `git checkout -b feature/amazing-feature`
4. 提交更改: `git commit -m 'Add amazing feature'`
5. 推送到分支: `git push origin feature/amazing-feature`
6. 创建 Pull Request

## 📚 文档

- [📊 项目状态总结](PROJECT_STATUS_SUMMARY.md)
- [🚀 未来优化方向](FUTURE_OPTIMIZATION.md)
- [⚡ 快速启动指南](QUICK_START.md)
- [📋 产品需求文档](docs/PRD.md)
- [🛠️ 部署指南](DEPLOYMENT.md)

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

---

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**