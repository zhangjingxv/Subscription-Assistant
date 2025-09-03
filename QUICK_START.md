# 快速开始指南

## 3分钟启动

### 方式1：一键脚本（推荐）

```bash
./INSTANT_START.sh
```

完成！系统已运行在 http://localhost:8000

### 方式2：手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r api/requirements-minimal.txt

# 3. 配置环境
cp .env.example .env

# 4. 启动服务
cd api
uvicorn app.main:app --reload
```

## 测试系统

### 1. 检查健康状态
```bash
curl http://localhost:8000/health
```

### 2. 使用测试账号
- 邮箱: test@example.com
- 密码: test123

### 3. 访问API文档
打开浏览器访问: http://localhost:8000/docs

## 添加RSS源

```bash
# 获取认证Token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=test123" \
  | jq -r .access_token)

# 添加RSS源
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacker News",
    "url": "https://news.ycombinator.com/rss",
    "type": "rss"
  }'
```

## 常见问题

### 端口被占用
```bash
# 查找占用8000端口的进程
lsof -i :8000

# 使用其他端口
uvicorn app.main:app --port 8001
```

### 数据库连接失败
```bash
# 检查数据库配置
echo $DATABASE_URL

# 使用SQLite（无需配置）
DATABASE_URL=sqlite:///./attentionsync.db
```

### 依赖安装失败
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 下一步

1. [部署到生产环境](./DEPLOYMENT.md)
2. [查看API文档](http://localhost:8000/docs)
3. [配置定时任务](./docs/celery.md)