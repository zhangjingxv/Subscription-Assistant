#!/bin/bash
# AttentionSync 简单启动脚本 - 哥，这个更直接

set -e

echo "🚀 AttentionSync 简单启动"
echo "========================"

# 检查Python版本
echo -n "检查Python版本... "
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "✓ Python $PYTHON_VERSION"
else
    echo "✗ Python版本过低"
    exit 1
fi

# 创建环境配置
echo -n "配置环境... "
if [ ! -f ".env" ]; then
    cat > .env << EOF
ENVIRONMENT=development
DATABASE_URL=sqlite:///./attentionsync.db
SECRET_KEY=dev-secret-key-$(date +%s)
JWT_SECRET=dev-jwt-secret-$(date +%s)
LOG_LEVEL=INFO
EOF
    echo "✓"
else
    echo "已存在"
fi

# 安装依赖到用户目录
echo "安装依赖到用户目录..."
python3 -m pip install --user --break-system-packages -q fastapi uvicorn sqlalchemy feedparser pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-dotenv httpx

# 初始化数据库
echo "初始化数据库..."
cd api
python3 << EOF
import sys
import os
sys.path.insert(0, os.getcwd())
from app.core.db import init_db
init_db()
print("数据库初始化成功")
EOF
cd ..

# 创建测试用户
echo "创建测试用户..."
cd api
python3 << EOF
import sys
import os
sys.path.insert(0, os.getcwd())
from app.core.db import get_db
from app.models.user import User
from app.core.security import get_password_hash

def create_user():
    for db in get_db():
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if not existing:
            user = User(
                email="test@example.com",
                hashed_password=get_password_hash("test123"),
                is_active=True
            )
            db.add(user)
            db.commit()
            print("✓ 测试用户创建成功")
            print("  邮箱: test@example.com")
            print("  密码: test123")
        else:
            print("✓ 测试用户已存在")
        break

create_user()
EOF
cd ..

echo ""
echo "🎯 启动服务..."
echo "========================"
echo "API文档: http://localhost:8000/docs"
echo "健康检查: curl http://localhost:8000/health"
echo "测试账号: test@example.com / test123"
echo ""
echo "正在启动API服务..."

cd api
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload