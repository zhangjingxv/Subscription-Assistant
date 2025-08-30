# 🚀 AttentionSync 部署指南

## 📦 部署选项

### 1. Docker Compose 部署 (推荐)

适用于单机部署和开发环境。

```bash
# 克隆项目
git clone https://github.com/attentionsync/attentionsync.git
cd attentionsync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥

# 启动服务
docker compose up -d

# 初始化数据库
docker compose exec api python ../scripts/init_db.py

# 访问应用
# 前端: http://localhost:3000
# API: http://localhost:8000/docs
```

### 2. 本地开发部署

适用于开发和调试。

#### 前置要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

#### 后端部署
```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置数据库
export DATABASE_URL="postgresql://user:password@localhost:5432/attentionsync"
export REDIS_URL="redis://localhost:6379/0"

# 初始化数据库
python ../scripts/init_db.py

# 启动API服务
uvicorn app.main:app --reload --port 8000
```

#### Worker部署
```bash
cd worker
pip install -r requirements.txt

# 启动Worker
celery -A app.celery_app worker --loglevel=info

# 启动调度器 (新终端)
celery -A app.celery_app beat --loglevel=info
```

#### 前端部署
```bash
cd web
npm install
npm run build
npm start
```

### 3. 生产环境部署

#### 使用Docker Swarm
```bash
# 初始化Swarm
docker swarm init

# 部署Stack
docker stack deploy -c docker-compose.yml attentionsync
```

#### 使用Kubernetes
```bash
# 应用Kubernetes配置
kubectl apply -f infra/k8s/

# 查看部署状态
kubectl get pods -n attentionsync
```

## 🔧 环境配置

### 必需环境变量

```env
# 数据库
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://host:port/db

# 安全
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production

# AI服务 (至少配置一个)
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 可选配置

```env
# 应用设置
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# 限流
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# 内容处理
MAX_CONTENT_LENGTH=1000000
SUMMARY_MAX_LENGTH=200
WHISPER_MODEL=base
```

## 🔒 安全配置

### 1. 更新默认密钥
```bash
# 生成新的密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 更新 .env 文件
SECRET_KEY=新生成的密钥
JWT_SECRET=新生成的密钥
```

### 2. 数据库安全
```bash
# 更改默认数据库密码
POSTGRES_PASSWORD=强密码

# 限制数据库访问
# 在docker-compose.yml中移除ports映射
```

### 3. 反向代理配置
```nginx
# /etc/nginx/sites-available/attentionsync
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 监控配置

### 1. 启用监控服务
```bash
# 启动Prometheus和Grafana
docker compose --profile monitoring up -d
```

### 2. 访问监控界面
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### 3. 配置告警
```yaml
# prometheus/alerts.yml
groups:
  - name: attentionsync
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
```

## 🔄 备份策略

### 1. 数据库备份
```bash
# 创建备份
docker compose exec postgres pg_dump -U attentionsync attentionsync > backup.sql

# 恢复备份
docker compose exec -T postgres psql -U attentionsync attentionsync < backup.sql
```

### 2. 对象存储备份
```bash
# 备份MinIO数据
docker compose exec minio mc mirror /data /backup
```

### 3. 自动备份脚本
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec postgres pg_dump -U attentionsync attentionsync > "backup_${DATE}.sql"
gzip "backup_${DATE}.sql"
```

## 🚀 性能优化

### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_items_published_importance 
ON items(published_at DESC, importance_score DESC);

-- 配置连接池
max_connections = 100
shared_buffers = 256MB
```

### 2. Redis优化
```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
```

### 3. 应用优化
- 启用Gzip压缩
- 配置CDN
- 图片优化
- API响应缓存

## 🔧 故障排除

### 常见问题

1. **数据库连接失败**
```bash
# 检查数据库状态
docker compose logs postgres

# 重启数据库
docker compose restart postgres
```

2. **API服务启动失败**
```bash
# 检查API日志
docker compose logs api

# 验证环境变量
docker compose exec api env | grep -E "(DATABASE|REDIS)"
```

3. **Worker任务不执行**
```bash
# 检查Worker状态
docker compose logs worker

# 检查Redis连接
docker compose exec redis redis-cli ping
```

## 📞 技术支持

- 📖 文档: [docs.attentionsync.io](https://docs.attentionsync.io)
- 🐛 问题反馈: [GitHub Issues](https://github.com/attentionsync/attentionsync/issues)
- 💬 社区讨论: [Discord](https://discord.gg/attentionsync)
- 📧 邮箱支持: support@attentionsync.io

---

🎯 **部署成功后，您将拥有一个完全功能的智能信息聚合平台！**