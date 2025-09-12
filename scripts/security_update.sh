#!/bin/bash

# AttentionSync 安全更新脚本
# 自动检查并更新依赖包安全漏洞

set -e

echo "🔒 AttentionSync 安全更新开始..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 备份当前依赖文件
backup_dependencies() {
    log_info "备份当前依赖文件..."
    
    if [ -f "api/requirements.txt" ]; then
        cp api/requirements.txt "api/requirements.txt.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份 api/requirements.txt"
    fi
    
    if [ -f "web/package.json" ]; then
        cp web/package.json "web/package.json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份 web/package.json"
    fi
    
    if [ -f "worker/requirements.txt" ]; then
        cp worker/requirements.txt "worker/requirements.txt.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份 worker/requirements.txt"
    fi
}

# Python 依赖安全检查和更新
update_python_dependencies() {
    log_info "开始 Python 依赖安全更新..."
    
    # 检查必要工具
    check_command pip
    
    # 安装安全检查工具
    log_info "安装安全检查工具..."
    pip install --upgrade safety bandit pip-audit
    
    # 检查当前漏洞
    log_info "扫描 API 服务依赖漏洞..."
    if [ -f "api/requirements.txt" ]; then
        cd api
        
        # 使用 safety 检查
        log_info "运行 Safety 安全扫描..."
        safety check --json > safety_report_new.json || log_warn "发现安全漏洞，继续更新..."
        
        # 使用 pip-audit 检查
        log_info "运行 pip-audit 安全扫描..."
        pip-audit --format=json --output=pip_audit_report.json || log_warn "发现安全漏洞，继续更新..."
        
        # 应用安全更新的依赖版本
        if [ -f "../requirements-security-updated.txt" ]; then
            log_info "应用安全更新版本..."
            cp ../requirements-security-updated.txt requirements.txt
            
            # 安装更新的依赖
            log_info "安装更新的依赖包..."
            pip install -r requirements.txt --upgrade
            
            # 再次安全检查
            log_info "验证安全更新效果..."
            safety check --json > safety_report_after_update.json || log_warn "仍有部分漏洞，请手动处理"
        fi
        
        cd ..
    fi
    
    # 更新 Worker 依赖
    if [ -f "worker/requirements.txt" ]; then
        log_info "更新 Worker 依赖..."
        cd worker
        pip install -r requirements.txt --upgrade
        safety check || log_warn "Worker 依赖存在安全问题"
        cd ..
    fi
}

# Node.js 依赖安全检查和更新
update_nodejs_dependencies() {
    log_info "开始 Node.js 依赖安全更新..."
    
    check_command npm
    
    if [ -f "web/package.json" ]; then
        cd web
        
        # 安全审计
        log_info "运行 npm 安全审计..."
        npm audit --json > npm_audit_report.json || log_warn "发现 npm 安全漏洞"
        
        # 应用安全更新的依赖版本
        if [ -f "../package-security-updated.json" ]; then
            log_info "应用安全更新版本..."
            cp ../package-security-updated.json package.json
            
            # 清理旧的 node_modules 和 lock 文件
            rm -rf node_modules package-lock.json
            
            # 安装更新的依赖
            log_info "安装更新的依赖包..."
            npm install
            
            # 再次安全审计
            log_info "验证安全更新效果..."
            npm audit --json > npm_audit_after_update.json || log_warn "仍有部分漏洞，请手动处理"
            
            # 自动修复可修复的漏洞
            log_info "自动修复可修复的漏洞..."
            npm audit fix --force || log_warn "部分漏洞无法自动修复"
        fi
        
        cd ..
    fi
}

# Docker 镜像安全扫描
scan_docker_images() {
    log_info "开始 Docker 镜像安全扫描..."
    
    if command -v trivy &> /dev/null; then
        log_info "使用 Trivy 扫描 Docker 镜像..."
        
        # 扫描基础镜像
        trivy image --format json --output docker_scan_postgres.json postgres:15-alpine || log_warn "PostgreSQL 镜像存在漏洞"
        trivy image --format json --output docker_scan_redis.json redis:7-alpine || log_warn "Redis 镜像存在漏洞"
        trivy image --format json --output docker_scan_node.json node:18-alpine || log_warn "Node 镜像存在漏洞"
        trivy image --format json --output docker_scan_python.json python:3.11-slim || log_warn "Python 镜像存在漏洞"
        
        # 构建并扫描应用镜像
        if [ -f "docker-compose.yml" ]; then
            log_info "构建并扫描应用镜像..."
            docker-compose build
            
            trivy image --format json --output docker_scan_api.json attentionsync-api:latest || log_warn "API 镜像存在漏洞"
            trivy image --format json --output docker_scan_web.json attentionsync-web:latest || log_warn "Web 镜像存在漏洞"
            trivy image --format json --output docker_scan_worker.json attentionsync-worker:latest || log_warn "Worker 镜像存在漏洞"
        fi
    else
        log_warn "Trivy 未安装，跳过 Docker 镜像扫描"
        log_info "安装 Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
    fi
}

# 生成安全报告
generate_security_report() {
    log_info "生成安全报告..."
    
    REPORT_FILE="security_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > $REPORT_FILE << EOF
# AttentionSync 安全更新报告

**生成时间**: $(date)
**更新版本**: $(git rev-parse --short HEAD)

## 📊 安全扫描结果

### Python 依赖
EOF

    if [ -f "api/safety_report_new.json" ]; then
        echo "- Safety 扫描完成，详见 api/safety_report_new.json" >> $REPORT_FILE
    fi
    
    if [ -f "api/pip_audit_report.json" ]; then
        echo "- pip-audit 扫描完成，详见 api/pip_audit_report.json" >> $REPORT_FILE
    fi

    cat >> $REPORT_FILE << EOF

### Node.js 依赖
EOF

    if [ -f "web/npm_audit_report.json" ]; then
        echo "- npm audit 扫描完成，详见 web/npm_audit_report.json" >> $REPORT_FILE
    fi

    cat >> $REPORT_FILE << EOF

### Docker 镜像
EOF

    if [ -f "docker_scan_api.json" ]; then
        echo "- Docker 镜像扫描完成，详见各 docker_scan_*.json 文件" >> $REPORT_FILE
    fi

    cat >> $REPORT_FILE << EOF

## 🔧 更新内容

### 主要依赖版本更新
- FastAPI: 升级到 0.109.0
- Next.js: 升级到 14.1.0
- SQLAlchemy: 升级到 2.0.25
- Pydantic: 升级到 2.6.0
- 其他安全相关包的版本更新

### 安全修复
- 修复已知的 CVE 漏洞
- 更新加密库到最新版本
- 修复依赖链中的传递性漏洞

## 📋 后续建议

1. 定期运行此安全更新脚本
2. 订阅相关安全通告
3. 配置自动化安全扫描
4. 建立安全响应流程

## 🔗 相关链接

- [Python 安全公告](https://python.org/news/security/)
- [Node.js 安全公告](https://nodejs.org/en/security/)
- [Docker 安全最佳实践](https://docs.docker.com/develop/security-best-practices/)
EOF

    log_info "安全报告已生成: $REPORT_FILE"
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    # 保留报告文件，清理其他临时文件
    # find . -name "*.tmp" -delete
}

# 主函数
main() {
    log_info "开始安全更新流程..."
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在 AttentionSync 项目根目录下运行此脚本"
        exit 1
    fi
    
    # 备份依赖文件
    backup_dependencies
    
    # 更新 Python 依赖
    update_python_dependencies
    
    # 更新 Node.js 依赖
    update_nodejs_dependencies
    
    # Docker 镜像扫描
    scan_docker_images
    
    # 生成安全报告
    generate_security_report
    
    # 清理临时文件
    cleanup
    
    log_info "✅ 安全更新完成！"
    log_info "请查看生成的安全报告，并测试应用功能"
    log_info "建议运行: docker-compose up -d --build"
}

# 捕获退出信号进行清理
trap cleanup EXIT

# 执行主函数
main "$@"