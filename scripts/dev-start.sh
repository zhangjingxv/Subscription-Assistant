#!/bin/bash

# AttentionSync Development Environment Startup
# 开发环境启动脚本 - 仅启动基础服务

set -e

echo "🔧 AttentionSync 开发环境启动"
echo "============================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，添加必要的API密钥"
fi

echo "🐳 启动基础服务 (PostgreSQL, Redis, MinIO)..."
docker compose -f docker-compose.dev.yml up -d

echo "⏳ 等待服务启动..."
sleep 15

echo "🗄️  初始化数据库..."
cd api
python -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt -q
python ../scripts/init_db.py
cd ..

echo ""
echo "✅ 开发环境基础服务启动完成！"
echo ""
echo "🚀 下一步 - 启动开发服务器："
echo ""
echo "📡 启动API服务器:"
echo "   cd api && source venv/bin/activate && uvicorn app.main:app --reload"
echo ""
echo "🌐 启动前端服务器:"
echo "   cd web && npm install && npm run dev"
echo ""
echo "⚙️ 启动Worker (可选):"
echo "   cd worker && celery -A app.celery_app worker --loglevel=info"
echo ""
echo "📊 访问地址："
echo "   - 数据库: localhost:5432"
echo "   - Redis: localhost:6379" 
echo "   - MinIO: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "🛑 停止服务: docker compose -f docker-compose.dev.yml down"