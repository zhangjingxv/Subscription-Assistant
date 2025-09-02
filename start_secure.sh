#!/bin/bash

# 🔒 AttentionSync 安全启动脚本
# 遵循Linus Torvalds的代码哲学: "安全不是功能，而是态度"

set -e  # 遇到错误立即退出

echo "🔒 AttentionSync 安全启动检查"
echo "================================"

# 检查Python版本
echo "📋 检查Python环境..."
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python版本: $python_version"

# 检查必要的模块
echo "📋 检查安全模块..."
python -c "from app.core.package_whitelist import validator; print('✅ 包白名单验证器')"
python -c "from app.core.security_config import secret_manager; print('✅ 密钥管理器')"
python -c "from app.core.secure_subprocess import secure_subprocess; print('✅ 安全子进程')"
python -c "from app.core.exception_handler import exception_handler; print('✅ 异常处理器')"

# 检查环境变量
echo "📋 检查环境变量..."
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  警告: SECRET_KEY未设置，将使用自动生成的密钥"
else
    echo "✅ SECRET_KEY已设置"
fi

if [ -z "$JWT_SECRET" ]; then
    echo "⚠️  警告: JWT_SECRET未设置，将使用自动生成的密钥"
else
    echo "✅ JWT_SECRET已设置"
fi

if [ -z "$ENVIRONMENT" ]; then
    echo "⚠️  警告: ENVIRONMENT未设置，默认使用development"
    export ENVIRONMENT="development"
else
    echo "✅ ENVIRONMENT设置为: $ENVIRONMENT"
fi

# 安全验证
echo "📋 运行安全验证..."
python -c "
from app.core.package_whitelist import validator
from app.core.secure_subprocess import secure_subprocess

# 测试包白名单
assert validator.is_package_allowed('torch') == True
assert validator.is_package_allowed('evil-package') == False

# 测试命令白名单
assert 'pip' in secure_subprocess.ALLOWED_COMMANDS
assert 'invalid_command' not in secure_subprocess.ALLOWED_COMMANDS

print('✅ 所有安全验证通过')
"

# 启动应用
echo "🚀 启动AttentionSync API..."
echo "📍 服务地址: http://127.0.0.1:8000"
echo "🔒 安全模式: 已启用"
echo "📊 健康检查: http://127.0.0.1:8000/health"
echo ""

# 启动应用
exec python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
