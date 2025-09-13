# AttentionSync 全球化部署指南

## 🌍 概述

本指南将帮助您将 AttentionSync 部署为一个真正的全球化平台，支持多区域、多语言、高性能和合规要求。

## 📋 前置要求

### 基础设施要求
- Kubernetes 集群（v1.24+）
- 多区域云服务提供商（AWS/GCP/Azure）
- CDN服务（Cloudflare 推荐）
- 域名和SSL证书

### 服务依赖
- PostgreSQL 数据库集群
- Redis 集群
- 对象存储（S3兼容）
- 消息队列（RabbitMQ/Redis）

### 外部服务
- AI服务（OpenAI/Anthropic）
- 支付服务（Stripe/PayPal）
- 监控服务（Prometheus/Grafana）
- 日志服务（ELK Stack）

## 🚀 部署步骤

### 第一阶段：基础设施准备

#### 1. 创建Kubernetes集群

```bash
# 使用 AWS EKS 创建多区域集群
eksctl create cluster \
  --name attentionsync-global \
  --version 1.24 \
  --region us-east-1 \
  --zones us-east-1a,us-east-1b,us-east-1c \
  --nodegroup-name global-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 50 \
  --managed

# 欧洲集群
eksctl create cluster \
  --name attentionsync-europe \
  --version 1.24 \
  --region eu-west-1 \
  --zones eu-west-1a,eu-west-1b,eu-west-1c \
  --nodegroup-name europe-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 50 \
  --managed

# 亚太集群
eksctl create cluster \
  --name attentionsync-asia \
  --version 1.24 \
  --region ap-southeast-1 \
  --zones ap-southeast-1a,ap-southeast-1b,ap-southeast-1c \
  --nodegroup-name asia-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 50 \
  --managed
```

#### 2. 安装必要的Kubernetes组件

```bash
# 安装 NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.5.1/deploy/static/provider/aws/deploy.yaml

# 安装 Cert-Manager (SSL证书管理)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.0/cert-manager.yaml

# 安装 Metrics Server (HPA支持)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 安装 Prometheus + Grafana (监控)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

#### 3. 配置数据库集群

```sql
-- 创建全球化数据库架构
-- 执行 /workspace/infra/schemas.sql 中的SQL脚本

-- 美洲区域数据库
CREATE DATABASE attentionsync_americas;

-- 欧洲区域数据库  
CREATE DATABASE attentionsync_europe;

-- 亚太区域数据库
CREATE DATABASE attentionsync_asia;

-- 创建用户和权限
CREATE USER attentionsync_app WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE attentionsync_americas TO attentionsync_app;
GRANT ALL PRIVILEGES ON DATABASE attentionsync_europe TO attentionsync_app;
GRANT ALL PRIVILEGES ON DATABASE attentionsync_asia TO attentionsync_app;
```

### 第二阶段：应用部署

#### 1. 创建配置文件

```bash
# 创建命名空间和配置
kubectl apply -f infra/kubernetes/global-deployment.yaml

# 更新Secret配置（替换为实际值）
kubectl create secret generic attentionsync-secrets \
  --namespace=attentionsync-global \
  --from-literal=SECRET_KEY="your-secret-key-here" \
  --from-literal=JWT_SECRET_AMERICAS="your-jwt-secret-americas" \
  --from-literal=JWT_SECRET_EUROPE="your-jwt-secret-europe" \
  --from-literal=JWT_SECRET_ASIA="your-jwt-secret-asia" \
  --from-literal=DATABASE_URL_AMERICAS="postgresql://user:pass@americas-db:5432/attentionsync" \
  --from-literal=DATABASE_URL_EUROPE="postgresql://user:pass@europe-db:5432/attentionsync" \
  --from-literal=DATABASE_URL_ASIA="postgresql://user:pass@asia-db:5432/attentionsync" \
  --from-literal=REDIS_URL_AMERICAS="redis://americas-redis:6379/0" \
  --from-literal=REDIS_URL_EUROPE="redis://europe-redis:6379/0" \
  --from-literal=REDIS_URL_ASIA="redis://asia-redis:6379/0" \
  --from-literal=ANTHROPIC_API_KEY="your-anthropic-api-key" \
  --from-literal=OPENAI_API_KEY="your-openai-api-key" \
  --from-literal=STRIPE_SECRET_KEY="your-stripe-secret-key"
```

#### 2. 构建和推送Docker镜像

```bash
# 构建API镜像
cd api
docker build -t attentionsync/api:latest .
docker tag attentionsync/api:latest your-registry/attentionsync/api:latest
docker push your-registry/attentionsync/api:latest

# 构建Web镜像
cd ../web
docker build -t attentionsync/web:latest .
docker tag attentionsync/web:latest your-registry/attentionsync/web:latest
docker push your-registry/attentionsync/web:latest

# 构建Worker镜像
cd ../worker
docker build -t attentionsync/worker:latest .
docker tag attentionsync/worker:latest your-registry/attentionsync/worker:latest
docker push your-registry/attentionsync/worker:latest
```

#### 3. 部署应用

```bash
# 部署到所有区域
kubectl apply -f infra/kubernetes/global-deployment.yaml

# 检查部署状态
kubectl get pods -n attentionsync-global
kubectl get services -n attentionsync-global
kubectl get ingress -n attentionsync-global

# 查看日志
kubectl logs -f deployment/attentionsync-api-americas -n attentionsync-global
kubectl logs -f deployment/attentionsync-api-europe -n attentionsync-global
kubectl logs -f deployment/attentionsync-api-asia -n attentionsync-global
```

### 第三阶段：CDN和DNS配置

#### 1. 配置Cloudflare CDN

```javascript
// Cloudflare Worker 脚本用于智能路由
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const country = request.cf.country
  const continent = request.cf.continent
  
  // 基于地理位置路由
  let region = 'americas'
  
  if (['DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'SE', 'DK', 'FI', 'IE', 'PT', 'GR', 'CZ', 'HU', 'PL', 'SK', 'SI', 'EE', 'LV', 'LT', 'LU', 'MT', 'CY', 'BG', 'RO', 'HR'].includes(country)) {
    region = 'europe'
  } else if (['CN', 'JP', 'KR', 'SG', 'MY', 'TH', 'VN', 'PH', 'ID', 'IN', 'AU', 'NZ'].includes(country)) {
    region = 'asia_pacific'
  }
  
  // 构建目标URL
  const url = new URL(request.url)
  url.hostname = `${region}.api.attentionsync.io`
  
  // 添加地理信息头
  const modifiedRequest = new Request(url.toString(), {
    body: request.body,
    headers: {
      ...request.headers,
      'CF-IPCountry': country,
      'CF-Continent': continent,
      'X-Forwarded-For': request.headers.get('CF-Connecting-IP'),
    },
    method: request.method,
  })
  
  return fetch(modifiedRequest)
}
```

#### 2. DNS配置

```dns
# 主域名
attentionsync.io.           300 IN A     104.16.1.1
www.attentionsync.io.       300 IN CNAME attentionsync.io.

# API端点
api.attentionsync.io.       300 IN CNAME attentionsync.io.
americas.api.attentionsync.io. 300 IN A  52.1.1.1
europe.api.attentionsync.io.   300 IN A  3.1.1.1
asia.api.attentionsync.io.     300 IN A  13.1.1.1

# CDN端点
cdn.attentionsync.io.       300 IN CNAME attentionsync.io.
americas.cdn.attentionsync.io. 300 IN CNAME d1234567890.cloudfront.net.
europe.cdn.attentionsync.io.   300 IN CNAME d0987654321.cloudfront.net.
asia.cdn.attentionsync.io.     300 IN CNAME d1122334455.cloudfront.net.
```

### 第四阶段：监控和日志

#### 1. 配置Prometheus监控

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
      - job_name: 'attentionsync-api'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - attentionsync-global
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: attentionsync-api
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
```

#### 2. 配置告警规则

```yaml
# alert-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: attentionsync-alerts
  namespace: monitoring
spec:
  groups:
  - name: attentionsync.rules
    rules:
    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is above 1 second"
    
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Error rate is above 1%"
    
    - alert: LowCacheHitRate
      expr: cache_hit_rate < 0.8
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Low cache hit rate"
        description: "Cache hit rate is below 80%"
```

## 🔧 配置优化

### 1. 性能优化配置

```yaml
# performance-tuning.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-config
  namespace: attentionsync-global
data:
  # 数据库连接池配置
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "30"
  DB_POOL_TIMEOUT: "30"
  DB_POOL_RECYCLE: "3600"
  
  # Redis配置
  REDIS_POOL_SIZE: "50"
  REDIS_POOL_TIMEOUT: "10"
  
  # 缓存配置
  CACHE_DEFAULT_TTL: "3600"
  CACHE_MAX_SIZE: "1000"
  
  # API限流配置
  RATE_LIMIT_PER_MINUTE: "1000"
  RATE_LIMIT_BURST: "100"
  
  # 工作进程配置
  WORKER_CONCURRENCY: "10"
  WORKER_MAX_TASKS_PER_CHILD: "1000"
```

### 2. 安全配置

```yaml
# security-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-config
  namespace: attentionsync-global
data:
  # JWT配置
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRE_MINUTES: "1440"
  
  # 密码策略
  PASSWORD_MIN_LENGTH: "8"
  PASSWORD_REQUIRE_UPPERCASE: "true"
  PASSWORD_REQUIRE_LOWERCASE: "true"
  PASSWORD_REQUIRE_DIGITS: "true"
  PASSWORD_REQUIRE_SPECIAL: "true"
  
  # 会话配置
  SESSION_TIMEOUT: "3600"
  MAX_LOGIN_ATTEMPTS: "5"
  LOCKOUT_DURATION: "1800"
  
  # CORS配置
  CORS_ORIGINS: "https://attentionsync.io,https://www.attentionsync.io"
  CORS_METHODS: "GET,POST,PUT,DELETE,OPTIONS"
  CORS_HEADERS: "Content-Type,Authorization,X-Requested-With"
```

## 📊 监控和维护

### 1. 关键指标监控

```bash
# 检查应用健康状态
kubectl get pods -n attentionsync-global -o wide

# 查看资源使用情况
kubectl top pods -n attentionsync-global
kubectl top nodes

# 查看HPA状态
kubectl get hpa -n attentionsync-global

# 查看服务状态
kubectl get services -n attentionsync-global
kubectl get ingress -n attentionsync-global
```

### 2. 日志管理

```bash
# 查看应用日志
kubectl logs -f deployment/attentionsync-api-americas -n attentionsync-global --tail=100

# 查看错误日志
kubectl logs deployment/attentionsync-api-americas -n attentionsync-global | grep ERROR

# 导出日志到文件
kubectl logs deployment/attentionsync-api-americas -n attentionsync-global > americas-api.log
```

### 3. 备份和恢复

```bash
# 数据库备份
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual -n attentionsync-global

# 配置备份
kubectl get configmap attentionsync-global-config -n attentionsync-global -o yaml > config-backup.yaml
kubectl get secret attentionsync-secrets -n attentionsync-global -o yaml > secrets-backup.yaml

# 恢复配置
kubectl apply -f config-backup.yaml
kubectl apply -f secrets-backup.yaml
```

## 🚀 扩展和升级

### 1. 水平扩展

```bash
# 手动扩展Pod数量
kubectl scale deployment attentionsync-api-americas --replicas=10 -n attentionsync-global

# 更新HPA配置
kubectl patch hpa attentionsync-api-americas-hpa -n attentionsync-global -p '{"spec":{"maxReplicas":100}}'
```

### 2. 版本升级

```bash
# 滚动更新
kubectl set image deployment/attentionsync-api-americas api=attentionsync/api:v2.0.0 -n attentionsync-global

# 检查更新状态
kubectl rollout status deployment/attentionsync-api-americas -n attentionsync-global

# 回滚到上一版本
kubectl rollout undo deployment/attentionsync-api-americas -n attentionsync-global
```

## 🔍 故障排查

### 常见问题和解决方案

#### 1. Pod启动失败
```bash
# 查看Pod状态
kubectl describe pod <pod-name> -n attentionsync-global

# 查看事件
kubectl get events -n attentionsync-global --sort-by='.lastTimestamp'

# 检查资源限制
kubectl describe node <node-name>
```

#### 2. 数据库连接问题
```bash
# 测试数据库连接
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql -h <db-host> -U <username> -d <database>

# 查看数据库日志
kubectl logs <postgres-pod> -n database
```

#### 3. 缓存问题
```bash
# 测试Redis连接
kubectl run -it --rm debug --image=redis:7 --restart=Never -- redis-cli -h <redis-host> ping

# 清理缓存
kubectl run -it --rm debug --image=redis:7 --restart=Never -- redis-cli -h <redis-host> flushall
```

## 📈 性能优化建议

### 1. 数据库优化
- 使用读写分离
- 配置连接池
- 添加适当的索引
- 定期分析查询性能

### 2. 缓存优化
- 使用多层缓存策略
- 设置合适的TTL
- 监控缓存命中率
- 定期清理过期缓存

### 3. 网络优化
- 使用CDN加速静态资源
- 启用Gzip压缩
- 优化图片大小和格式
- 使用HTTP/2

### 4. 应用优化
- 异步处理耗时任务
- 实现断路器模式
- 使用连接池
- 优化数据库查询

## 🔐 安全最佳实践

### 1. 网络安全
- 使用Network Policy限制Pod间通信
- 配置WAF规则
- 启用TLS加密
- 定期更新证书

### 2. 身份认证
- 使用强密码策略
- 启用多因素认证
- 定期轮换API密钥
- 实现细粒度权限控制

### 3. 数据保护
- 加密敏感数据
- 定期备份数据
- 实现数据脱敏
- 遵守数据保护法规

## 📞 支持和联系

- 📧 技术支持: support@attentionsync.io
- 📚 文档中心: https://docs.attentionsync.io
- 💬 社区论坛: https://community.attentionsync.io
- 🐛 问题反馈: https://github.com/attentionsync/issues

---

*本部署指南将帮助您成功部署AttentionSync全球化平台。如有任何问题，请联系我们的技术支持团队。*