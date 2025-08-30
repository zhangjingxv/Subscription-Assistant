#!/bin/bash

# AttentionSync Quick Start Script
# 快速启动AttentionSync开发环境

set -e

echo "🚀 AttentionSync 快速启动脚本"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，添加必要的API密钥："
    echo "   - ANTHROPIC_API_KEY (推荐) 或 OPENAI_API_KEY"
    echo "   - 其他配置可以使用默认值"
    echo ""
    read -p "是否现在编辑 .env 文件？(y/n): " edit_env
    if [ "$edit_env" = "y" ]; then
        ${EDITOR:-nano} .env
    fi
fi

echo ""
echo "🐳 启动服务..."

# Start services with Docker Compose
docker-compose up -d postgres redis minio

echo "⏳ 等待数据库启动..."
sleep 10

# Initialize database
echo "🗄️  初始化数据库..."
cd api && python ../scripts/init_db.py
cd ..

echo "🚀 启动应用服务..."
docker-compose up -d api worker web

echo ""
echo "✅ AttentionSync 启动完成！"
echo ""
echo "📱 访问地址："
echo "   - 前端界面: http://localhost:3000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - MinIO控制台: http://localhost:9001"
echo ""
echo "👤 默认管理员账号："
echo "   - 邮箱: admin@attentionsync.io"
echo "   - 密码: admin123"
echo ""
echo "📊 查看服务状态: docker-compose ps"
echo "📝 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"