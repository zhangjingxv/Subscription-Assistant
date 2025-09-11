# AttentionSync 生产环境部署指南

## 📋 部署前检查清单

### 🔧 系统要求

**最低配置**：
- CPU: 2 核心
- 内存: 4GB RAM  
- 存储: 20GB SSD
- 网络: 100Mbps

**推荐配置**：
- CPU: 4 核心
- 内存: 8GB RAM
- 存储: 50GB SSD
- 网络: 1Gbps

**操作系统**：
- Ubuntu 20.04+ LTS
- CentOS 8+
- Docker 20.10+
- Docker Compose 2.0+

### 🛡️ 安全准备

1. **SSL 证书**
   ```bash
   # 使用 Let's Encrypt 获取免费证书
   sudo certbot certonly --standalone -d your-domain.com
   ```

2. **防火墙配置**
   ```bash
   # 开放必要端口
   sudo ufw allow 80/tcp      # HTTP
   sudo ufw allow 443/tcp     # HTTPS  
   sudo ufw allow 22/tcp      # SSH
   sudo ufw enable
   ```

3. **SSH 密钥认证**
   ```bash
   # 禁用密码认证，仅使用密钥
   sudo vim /etc/ssh/sshd_config
   # PasswordAuthentication no
   # PubkeyAuthentication yes
   ```

## 🚀 快速部署

### 1. 环境准备

```bash
# 克隆代码
git clone https://github.com/yourusername/attentionsync.git
cd attentionsync

# 复制生产环境配置
cp .env.production .env

# 编辑配置文件 - ⚠️ 必须修改所有 CHANGE_ME 值
vim .env
```

### 2. 配置文件修改

**必须修改的配置项**：
```bash
# 生成强密钥
openssl rand -hex 32  # 用于 SECRET_KEY
openssl rand -hex 32  # 用于 JWT_SECRET

# 数据库密码
POSTGRES_PASSWORD=your_super_secure_db_password_here

# MinIO 密钥
MINIO_ROOT_USER=admin_user_name
MINIO_ROOT_PASSWORD=super_secure_minio_password

# API 密钥
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# 域名配置
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_WS_URL=wss://your-domain.com/ws
```

### 3. 启动服务

```bash
# 拉取镜像并启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
docker-compose exec api python -m alembic upgrade head

# 创建管理员用户
docker-compose exec api python scripts/create_admin.py
```

### 5. 验证部署

```bash
# 健康检查
curl https://your-domain.com/health

# API 文档
curl https://your-domain.com/docs

# 前端页面
curl https://your-domain.com/
```

## 🔍 监控设置

### 启用监控服务

```bash
# 启动监控组件
docker-compose --profile monitoring up -d

# 访问监控面板
# Prometheus: http://your-domain.com:9090
# Grafana: http://your-domain.com:3001 (admin/admin)
```

### 配置告警

1. **Grafana 仪表盘导入**
   - 访问 Grafana
   - 导入 `infra/grafana/dashboards/` 中的仪表盘

2. **告警通知设置**
   ```bash
   # 配置邮件告警
   vim infra/grafana/provisioning/notifiers/email.yml
   
   # 配置 Slack 告警
   vim infra/grafana/provisioning/notifiers/slack.yml
   ```

## 🔄 日常运维

### 备份策略

**自动备份脚本**：
```bash
#!/bin/bash
# 每日备份脚本 /opt/attentionsync/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/attentionsync"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
docker-compose exec -T postgres pg_dump -U attentionsync_prod attentionsync_prod > $BACKUP_DIR/db_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_$DATE.sql

# 保留30天备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# 上传到云存储（可选）
# aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://your-backup-bucket/
```

**设置 Crontab**：
```bash
# 添加到 crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/attentionsync/backup.sh >> /var/log/attentionsync-backup.log 2>&1
```

### 日志管理

**日志轮转配置**：
```bash
# /etc/logrotate.d/attentionsync
/var/lib/docker/containers/*/*-json.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

### 性能优化

**数据库优化**：
```bash
# 执行性能优化 SQL
docker-compose exec postgres psql -U attentionsync_prod -d attentionsync_prod -f /docker-entrypoint-initdb.d/performance_indexes.sql

# 定期更新统计信息
docker-compose exec postgres psql -U attentionsync_prod -d attentionsync_prod -c "ANALYZE;"

# 清理过期数据
docker-compose exec api python scripts/cleanup_old_data.py
```

## 🚨 故障排除

### 常见问题

**1. 容器启动失败**
```bash
# 检查日志
docker-compose logs api

# 检查配置
docker-compose config

# 重新构建镜像
docker-compose build --no-cache api
```

**2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U attentionsync_prod

# 检查连接配置
docker-compose exec api python -c "from app.core.db import engine; print(engine.url)"

# 重启数据库
docker-compose restart postgres
```

**3. Redis 连接失败**
```bash
# 检查 Redis 状态
docker-compose exec redis redis-cli ping

# 检查连接配置
docker-compose exec api python -c "import redis; r=redis.from_url('redis://redis:6379'); print(r.ping())"

# 重启 Redis
docker-compose restart redis
```

**4. 任务队列问题**
```bash
# 检查 Celery 工作进程
docker-compose exec worker celery -A app.celery_app inspect active

# 检查任务队列状态
docker-compose exec worker celery -A app.celery_app inspect stats

# 重启工作进程
docker-compose restart worker
```

### 性能问题诊断

**1. API 响应慢**
```bash
# 检查 API 指标
curl https://your-domain.com/metrics | grep http_request_duration

# 查看慢查询
docker-compose exec postgres psql -U attentionsync_prod -d attentionsync_prod -c "SELECT * FROM v_slow_queries;"

# 检查连接池状态
docker-compose logs api | grep "pool"
```

**2. 内存使用高**
```bash
# 检查容器内存使用
docker stats

# 检查系统内存
free -h

# 检查数据库内存
docker-compose exec postgres psql -U attentionsync_prod -d attentionsync_prod -c "SELECT * FROM pg_stat_activity;"
```

**3. 磁盘空间不足**
```bash
# 检查磁盘使用
df -h

# 清理 Docker 镜像
docker system prune -a

# 清理日志
journalctl --vacuum-time=7d
```

## 🔧 扩容指南

### 水平扩容

**API 服务扩容**：
```bash
# 增加 API 实例
docker-compose up -d --scale api=3

# 配置负载均衡器
# 编辑 nginx.conf，添加更多上游服务器
```

**Worker 扩容**：
```bash
# 增加 Worker 实例
docker-compose up -d --scale worker=5

# 监控队列长度
docker-compose exec worker celery -A app.celery_app inspect active_queues
```

### 垂直扩容

**增加资源限制**：
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 数据库扩容

**读写分离**：
```bash
# 设置 PostgreSQL 主从复制
# 1. 配置主库
# 2. 配置从库
# 3. 修改应用配置使用读写分离
```

## 🛡️ 安全加固

### SSL/TLS 配置

**Nginx SSL 配置**：
```nginx
# infra/nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

### 访问控制

**IP 白名单**：
```nginx
# 限制管理接口访问
location /admin {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
}
```

### 定期安全更新

```bash
#!/bin/bash
# 安全更新脚本

# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker-compose pull

# 重启服务
docker-compose up -d

# 检查安全漏洞
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image attentionsync-api:latest
```

## 📊 监控指标

### 关键指标

**业务指标**：
- 日活跃用户数 (DAU)
- 内容获取成功率
- AI 摘要生成成功率
- 平均响应时间

**技术指标**：
- API 请求量和错误率
- 数据库连接数和慢查询
- 缓存命中率
- 任务队列长度

**系统指标**：
- CPU 和内存使用率
- 磁盘空间使用
- 网络流量
- 容器健康状态

### 告警阈值建议

| 指标 | 警告阈值 | 严重阈值 |
|------|----------|----------|
| API 错误率 | 5% | 10% |
| API P95 延迟 | 1s | 2s |
| CPU 使用率 | 70% | 85% |
| 内存使用率 | 80% | 90% |
| 磁盘使用率 | 80% | 90% |
| 数据库连接数 | 80% | 95% |

## 🔄 更新和回滚

### 蓝绿部署

```bash
#!/bin/bash
# 蓝绿部署脚本

# 1. 拉取新版本
git pull origin main

# 2. 构建新镜像
docker-compose build

# 3. 启动新实例
docker-compose -f docker-compose.blue.yml up -d

# 4. 健康检查
curl -f http://localhost:8001/health || exit 1

# 5. 切换流量
# 更新负载均衡器配置

# 6. 停止旧实例
docker-compose -f docker-compose.green.yml down
```

### 快速回滚

```bash
#!/bin/bash
# 回滚脚本

# 1. 切换到上一个版本
git checkout HEAD~1

# 2. 重新部署
docker-compose down
docker-compose up -d

# 3. 验证服务
curl -f https://your-domain.com/health
```

## 📞 支持联系

- **技术支持**: tech-support@attentionsync.io
- **紧急联系**: +86-xxx-xxxx-xxxx
- **文档更新**: https://docs.attentionsync.io

---

**最后更新**: 2024-01-15  
**版本**: v1.0.0