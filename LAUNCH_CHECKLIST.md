# 🚀 AttentionSync 上线发布检查清单

## 📋 发布前最终检查（必须100%完成）

### 🔐 安全配置检查

- [ ] **密钥安全**
  - [ ] `SECRET_KEY` 已更改为强随机密钥（32位+）
  - [ ] `JWT_SECRET` 已设置独立密钥
  - [ ] `POSTGRES_PASSWORD` 已更改（8位+强密码）
  - [ ] `MINIO_ROOT_PASSWORD` 已更改
  - [ ] `GRAFANA_PASSWORD` 已更改

- [ ] **SSL/TLS 配置**
  - [ ] SSL 证书已安装
  - [ ] HTTPS 重定向已配置
  - [ ] 安全头已设置
  - [ ] 证书自动续期已配置

- [ ] **访问控制**
  - [ ] 防火墙规则已配置
  - [ ] API 限流已启用
  - [ ] 管理接口访问限制已设置
  - [ ] CORS 策略已配置

### ⚡ 性能配置检查

- [ ] **数据库优化**
  - [ ] 性能索引已应用
  - [ ] 连接池已配置
  - [ ] 统计信息已更新
  - [ ] 慢查询监控已启用

- [ ] **缓存配置**
  - [ ] Redis 集群已配置
  - [ ] 缓存策略已设置
  - [ ] 缓存监控已启用
  - [ ] 缓存预热已执行

- [ ] **前端优化**
  - [ ] 生产构建已完成
  - [ ] 静态资源压缩已启用
  - [ ] CDN 已配置（可选）
  - [ ] Service Worker 已注册

### 📊 监控配置检查

- [ ] **基础监控**
  - [ ] Prometheus 运行正常
  - [ ] Grafana 运行正常
  - [ ] 所有监控目标状态正常
  - [ ] 关键指标数据正常

- [ ] **告警配置**
  - [ ] 告警规则已测试
  - [ ] 通知渠道已配置
  - [ ] 告警阈值已调整
  - [ ] 告警测试已通过

- [ ] **日志系统**
  - [ ] 结构化日志已配置
  - [ ] 日志轮转已设置
  - [ ] 错误日志收集正常
  - [ ] 访问日志记录正常

### 🧪 功能测试检查

- [ ] **核心功能**
  - [ ] 用户注册流程正常
  - [ ] 用户登录流程正常
  - [ ] RSS 源添加正常
  - [ ] 内容获取正常
  - [ ] 3分钟日读功能正常

- [ ] **API 测试**
  - [ ] 所有 API 端点响应正常
  - [ ] 认证机制工作正常
  - [ ] 错误处理正确
  - [ ] 限流机制有效

- [ ] **前端测试**
  - [ ] 页面加载正常
  - [ ] 交互功能正常
  - [ ] 移动端适配良好
  - [ ] 错误处理友好

## 🏃 发布执行步骤

### Step 1: 最终代码准备
```bash
# 确保代码是最新版本
git pull origin main

# 运行最终测试
./scripts/run_tests.sh --type all --coverage

# 检查测试结果
cat test-reports/test-summary.md
```

### Step 2: 生产环境配置
```bash
# 复制生产配置
cp .env.production .env

# 编辑配置文件，替换所有 CHANGE_ME 值
vim .env

# 验证配置
python -c "
from api.app.core.config_validator import validate_config
result = validate_config()
print('配置验证:', '通过' if result['valid'] else '失败')
if result['errors']: 
    print('错误:', result['errors'])
"
```

### Step 3: 数据库准备
```bash
# 备份现有数据（如果有）
docker-compose exec postgres pg_dump -U attentionsync_prod attentionsync_prod > backup_$(date +%Y%m%d).sql

# 应用数据库迁移
docker-compose exec api python -m alembic upgrade head

# 应用性能优化
docker-compose exec postgres psql -U attentionsync_prod -d attentionsync_prod -f /docker-entrypoint-initdb.d/performance_indexes.sql
```

### Step 4: 服务部署
```bash
# 构建最新镜像
docker-compose build --no-cache

# 启动所有服务
docker-compose up -d

# 检查服务状态
docker-compose ps
./scripts/scale_deployment.sh --action health
```

### Step 5: 监控启动
```bash
# 启动监控服务
docker-compose --profile monitoring up -d

# 验证监控
curl http://localhost:9090/targets
curl http://localhost:3001/api/health
```

### Step 6: 性能验证
```bash
# 运行性能优化
./scripts/performance_optimization.sh

# 压力测试
ab -n 1000 -c 20 http://localhost:8000/health

# 检查关键指标
curl http://localhost:8000/metrics | grep http_request_duration
```

### Step 7: 域名和 SSL
```bash
# 配置域名解析
# A 记录: your-domain.com → 服务器IP
# CNAME 记录: www.your-domain.com → your-domain.com

# 获取 SSL 证书
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 更新 Nginx 配置
sudo cp infra/nginx.conf /etc/nginx/sites-available/attentionsync
sudo ln -s /etc/nginx/sites-available/attentionsync /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 🔍 发布后监控重点

### 前24小时重点监控
- **API 响应时间** - 目标 P95 < 500ms
- **错误率** - 目标 < 0.1%
- **用户注册成功率** - 目标 > 95%
- **内容获取成功率** - 目标 > 90%
- **系统资源使用** - CPU < 70%, 内存 < 80%

### 关键告警设置
```bash
# 设置关键告警（示例）
# API 服务下线 - 立即通知
# 错误率超过 5% - 5分钟内通知
# 响应时间超过 1秒 - 10分钟内通知
# 数据库连接失败 - 立即通知
# 磁盘空间不足 - 提前通知
```

## 📱 用户支持准备

### 用户文档
- [ ] 用户使用手册已准备
- [ ] 常见问题 FAQ 已准备
- [ ] 功能介绍视频已录制
- [ ] 客服联系方式已公布

### 技术支持
- [ ] 技术支持团队已就位
- [ ] 故障响应流程已建立
- [ ] 备用联系方式已准备
- [ ] 回滚方案已准备

## 🎊 发布成功标志

当以下所有指标达标时，可以宣布发布成功：

✅ **服务稳定运行** 24小时无重大故障  
✅ **用户注册** 成功率 > 95%  
✅ **核心功能** 3分钟日读功能正常  
✅ **性能指标** 所有关键指标达标  
✅ **监控告警** 系统运行正常  
✅ **用户反馈** 初期用户反馈积极  

---

## 💡 最后的建议

1. **保持冷静** - 发布过程中遇到问题是正常的，按照检查清单逐步解决

2. **实时监控** - 发布后密切关注监控面板，特别是前几个小时

3. **用户反馈** - 建立用户反馈渠道，快速响应用户问题

4. **持续优化** - 根据实际使用数据持续优化性能和用户体验

5. **备份重要** - 确保数据备份策略正常运行

**祝你发布成功！🎉**