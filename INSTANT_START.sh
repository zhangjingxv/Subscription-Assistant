#!/bin/bash
# AttentionSync 一键启动脚本
# 哥，这个脚本让你3分钟内跑起整个系统

set -e  # 遇错即停

echo "🚀 AttentionSync 快速启动程序"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python版本
check_python() {
    echo -n "检查Python版本... "
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ $(echo "$PYTHON_VERSION >= 3.8" | bc) -eq 1 ]; then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
            return 0
        else
            echo -e "${RED}✗${NC} Python版本过低: $PYTHON_VERSION (需要>=3.8)"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} 未找到Python3"
        return 1
    fi
}

# 创建虚拟环境
setup_venv() {
    echo -n "创建虚拟环境... "
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}已存在${NC}"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
}

# 安装最小依赖
install_deps() {
    echo "安装核心依赖..."
    
    # 创建最小依赖文件
    cat > requirements-minimal.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
feedparser==6.0.10
pydantic==2.5.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
httpx==0.25.2
EOF
    
    pip install -q --upgrade pip
    pip install -q -r requirements-minimal.txt
    echo -e "${GREEN}✓${NC} 依赖安装完成"
}

# 创建环境配置
setup_env() {
    echo -n "配置环境变量... "
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# AttentionSync 开发环境配置
ENVIRONMENT=development
DATABASE_URL=sqlite:///./attentionsync.db
SECRET_KEY=dev-secret-key-$(date +%s)
JWT_SECRET=dev-jwt-secret-$(date +%s)
LOG_LEVEL=INFO
EOF
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}已配置${NC}"
    fi
}

# 初始化数据库
init_database() {
    echo -n "初始化数据库... "
    python3 << EOF
import sys
sys.path.append('./api')
from app.core.db import init_db
import asyncio
asyncio.run(init_db())
print("数据库初始化成功")
EOF
    echo -e "${GREEN}✓${NC}"
}

# 创建测试用户
create_test_user() {
    echo "创建测试用户..."
    python3 << EOF
import sys
sys.path.append('./api')
from app.core.db import get_db
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_user():
    async for db in get_db():
        # 检查用户是否存在
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

asyncio.run(create_user())
EOF
}

# 添加示例RSS源
add_sample_sources() {
    echo "添加示例RSS源..."
    python3 << EOF
import sys
sys.path.append('./api')
from app.core.db import get_db
from app.models.source import Source
from app.models.user import User
import asyncio

async def add_sources():
    async for db in get_db():
        # 获取测试用户
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            # 示例RSS源列表
            sources = [
                ("Hacker News", "https://news.ycombinator.com/rss", "rss"),
                ("阮一峰的网络日志", "http://www.ruanyifeng.com/blog/atom.xml", "rss"),
                ("36氪", "https://www.36kr.com/feed", "rss"),
            ]
            
            for name, url, source_type in sources:
                existing = db.query(Source).filter(
                    Source.url == url,
                    Source.user_id == user.id
                ).first()
                
                if not existing:
                    source = Source(
                        name=name,
                        url=url,
                        type=source_type,
                        user_id=user.id,
                        is_active=True
                    )
                    db.add(source)
                    print(f"  ✓ 添加源: {name}")
            
            db.commit()
        break

asyncio.run(add_sources())
EOF
}

# 启动服务
start_services() {
    echo ""
    echo "🎯 启动服务..."
    echo "================================"
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ 端口8000已被占用${NC}"
        echo "请先停止占用端口的服务，或修改配置使用其他端口"
        exit 1
    fi
    
    echo -e "${GREEN}系统启动成功！${NC}"
    echo ""
    echo "📋 快速测试指南："
    echo "--------------------------------"
    echo "1. API文档: http://localhost:8000/docs"
    echo "2. 健康检查: curl http://localhost:8000/health"
    echo "3. 登录测试:"
    echo "   邮箱: test@example.com"
    echo "   密码: test123"
    echo ""
    echo "📌 常用命令："
    echo "--------------------------------"
    echo "停止服务: Ctrl+C"
    echo "查看日志: tail -f attentionsync.log"
    echo "重启服务: ./INSTANT_START.sh"
    echo ""
    echo "正在启动API服务..."
    echo "================================"
    
    # 启动API服务
    cd api
    python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
}

# 错误处理
handle_error() {
    echo -e "${RED}✗ 启动失败${NC}"
    echo "请检查错误信息并重试"
    exit 1
}

# 主流程
main() {
    # 设置错误处理
    trap handle_error ERR
    
    # 执行启动步骤
    check_python || exit 1
    setup_venv
    install_deps
    setup_env
    init_database
    create_test_user
    add_sample_sources
    start_services
}

# 运行主流程
main