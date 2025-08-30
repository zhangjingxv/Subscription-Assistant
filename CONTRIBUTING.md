# 🤝 贡献指南

感谢您对AttentionSync项目的关注！我们欢迎所有形式的贡献。

## 🌟 如何贡献

### 1. 报告问题
- 使用 [GitHub Issues](https://github.com/attentionsync/attentionsync/issues) 报告bug
- 提供详细的复现步骤
- 包含系统环境信息

### 2. 功能建议
- 在 [GitHub Discussions](https://github.com/attentionsync/attentionsync/discussions) 讨论新功能
- 参考 [MVP路线图](docs/MVP_ROADMAP.md) 了解开发计划

### 3. 代码贡献
1. Fork项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建Pull Request

## 🔧 开发环境设置

### 快速启动
```bash
# 启动开发环境基础服务
./scripts/dev-start.sh

# 启动API开发服务器
cd api && source venv/bin/activate && uvicorn app.main:app --reload

# 启动前端开发服务器
cd web && npm install && npm run dev
```

### 代码规范
- Python: 使用 `black` 格式化，`flake8` 检查
- TypeScript: 使用 `prettier` 格式化，`eslint` 检查
- 提交信息: 使用 [Conventional Commits](https://conventionalcommits.org/)

### 测试
```bash
# 后端测试
cd api && pytest

# 前端测试  
cd web && npm test
```

## 📋 开发任务

查看 [GitHub Projects](https://github.com/attentionsync/attentionsync/projects) 了解当前开发任务。

### 🚀 高优先级任务
- [ ] 视频转写功能实现
- [ ] 移动端PWA优化
- [ ] 性能优化
- [ ] 更多信息源支持

### 💡 欢迎贡献的领域
- 新的信息源适配器
- UI/UX改进
- 多语言支持
- 文档完善
- 测试用例

## 🎯 贡献者认可

所有贡献者都会在项目中获得认可：
- README.md 贡献者列表
- 每月贡献者报告
- 特殊贡献者徽章

## 📞 联系方式

- 💬 Discord: [AttentionSync社区](https://discord.gg/attentionsync)
- 📧 Email: contributors@attentionsync.io
- 🐦 Twitter: [@attentionsync](https://twitter.com/attentionsync)

感谢您的贡献！🙏