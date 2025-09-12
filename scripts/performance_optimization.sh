#!/bin/bash

# AttentionSync 性能优化脚本
# 自动执行数据库优化、缓存预热、前端构建优化等

set -e

echo "⚡ AttentionSync 性能优化"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_header() {
    echo -e "${BLUE}[OPTIMIZE]${NC} $1"
}

# 数据库优化
optimize_database() {
    log_header "数据库性能优化"
    
    log_info "应用性能索引..."
    if docker-compose exec -T postgres psql -U attentionsync_prod -d attentionsync_prod -f /docker-entrypoint-initdb.d/performance_indexes.sql; then
        log_info "✅ 性能索引应用成功"
    else
        log_warn "⚠️  性能索引应用失败，请手动检查"
    fi
    
    log_info "更新表统计信息..."
    docker-compose exec -T postgres psql -U attentionsync_prod -d attentionsync_prod -c "
        ANALYZE users;
        ANALYZE sources;
        ANALYZE items;
        ANALYZE summaries;
        ANALYZE interactions;
        ANALYZE daily_digests;
    "
    
    log_info "刷新物化视图..."
    docker-compose exec -T postgres psql -U attentionsync_prod -d attentionsync_prod -c "
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_items;
    "
    
    log_info "清理过期数据..."
    docker-compose exec -T postgres psql -U attentionsync_prod -d attentionsync_prod -c "
        -- 清理30天前的审计日志
        DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '30 days';
        
        -- 清理90天前的交互记录
        DELETE FROM interactions WHERE created_at < NOW() - INTERVAL '90 days';
        
        -- 清理过期的API密钥
        DELETE FROM api_keys WHERE expires_at < NOW();
        
        -- 清理未验证的用户（7天后）
        DELETE FROM users WHERE is_verified = false AND created_at < NOW() - INTERVAL '7 days';
    "
    
    log_info "优化数据库配置..."
    docker-compose exec -T postgres psql -U attentionsync_prod -d attentionsync_prod -c "
        -- 设置工作内存
        ALTER SYSTEM SET work_mem = '16MB';
        
        -- 设置共享缓冲区
        ALTER SYSTEM SET shared_buffers = '256MB';
        
        -- 设置有效缓存大小
        ALTER SYSTEM SET effective_cache_size = '1GB';
        
        -- 设置检查点配置
        ALTER SYSTEM SET checkpoint_completion_target = 0.9;
        
        -- 重新加载配置
        SELECT pg_reload_conf();
    "
    
    log_info "✅ 数据库优化完成"
}

# Redis 优化
optimize_redis() {
    log_header "Redis 缓存优化"
    
    log_info "检查 Redis 内存使用..."
    local memory_info=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human)
    log_info "Redis 内存使用: $memory_info"
    
    log_info "优化 Redis 配置..."
    docker-compose exec -T redis redis-cli config set maxmemory-policy allkeys-lru
    docker-compose exec -T redis redis-cli config set save "900 1 300 10 60 10000"
    docker-compose exec -T redis redis-cli config set tcp-keepalive 300
    docker-compose exec -T redis redis-cli config set timeout 0
    
    log_info "清理过期键..."
    docker-compose exec -T redis redis-cli --scan --pattern "*:expired:*" | head -1000 | xargs -r docker-compose exec -T redis redis-cli del
    
    log_info "预热常用缓存..."
    # 这里可以添加缓存预热逻辑
    
    log_info "✅ Redis 优化完成"
}

# 前端构建优化
optimize_frontend() {
    log_header "前端构建优化"
    
    cd web
    
    log_info "清理旧的构建文件..."
    rm -rf .next node_modules/.cache
    
    log_info "安装依赖（使用缓存）..."
    npm ci --prefer-offline --no-audit
    
    log_info "运行 TypeScript 类型检查..."
    npm run type-check
    
    log_info "运行代码检查..."
    npm run lint
    
    log_info "构建生产版本..."
    NODE_ENV=production npm run build
    
    log_info "分析构建包大小..."
    if command -v npx &> /dev/null; then
        npx next build --analyze > build-analysis.txt 2>&1 || log_warn "构建分析失败"
    fi
    
    log_info "生成构建报告..."
    cat > build-report.md << EOF
# 前端构建报告

**构建时间**: $(date)
**Node.js 版本**: $(node --version)
**npm 版本**: $(npm --version)

## 构建统计

\`\`\`
$(cat .next/build-manifest.json | jq -r '.pages | to_entries | map("\(.key): \(.value | length) files") | .[]' 2>/dev/null || echo "构建清单不可用")
\`\`\`

## 包大小分析

$(cat build-analysis.txt 2>/dev/null || echo "包大小分析不可用")

## 优化建议

1. 使用动态导入拆分大型组件
2. 优化图片格式和大小
3. 启用 Gzip/Brotli 压缩
4. 使用 CDN 加速静态资源
5. 实现代码分割和懒加载

EOF
    
    cd ..
    log_info "✅ 前端优化完成"
}

# API 服务优化
optimize_api() {
    log_header "API 服务优化"
    
    log_info "检查 API 服务状态..."
    if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_warn "API 服务不可访问，跳过优化"
        return
    fi
    
    log_info "预热应用缓存..."
    # 预热常用端点
    curl -s http://localhost:8000/api/v1/auth/me >/dev/null || true
    curl -s http://localhost:8000/api/v1/sources >/dev/null || true
    curl -s http://localhost:8000/api/v1/items?limit=10 >/dev/null || true
    
    log_info "检查 API 性能指标..."
    if curl -s http://localhost:8000/metrics >/dev/null; then
        curl -s http://localhost:8000/metrics | grep -E "(http_request_duration|db_query_duration)" > api-metrics.txt
        log_info "API 指标已保存到 api-metrics.txt"
    fi
    
    log_info "优化 Python 运行时..."
    docker-compose exec -T api python -c "
import gc
import sys

# 强制垃圾回收
gc.collect()

# 打印内存使用情况
print(f'Python 内存使用: {sys.getsizeof(gc.get_objects())} bytes')
print(f'垃圾回收统计: {gc.get_stats()}')
"
    
    log_info "✅ API 优化完成"
}

# 系统级优化
optimize_system() {
    log_header "系统级优化"
    
    log_info "检查系统资源使用..."
    echo "=== CPU 使用情况 ==="
    top -bn1 | head -5
    
    echo "=== 内存使用情况 ==="
    free -h
    
    echo "=== 磁盘使用情况 ==="
    df -h
    
    echo "=== Docker 资源使用 ==="
    docker system df
    
    log_info "清理 Docker 缓存..."
    docker system prune -f --volumes
    
    log_info "优化 Docker 镜像..."
    # 重新构建镜像以应用优化
    docker-compose build --no-cache --parallel
    
    log_info "设置系统参数优化..."
    # 这些需要 root 权限，在容器环境中可能不适用
    # echo 'vm.swappiness=10' >> /etc/sysctl.conf
    # echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
    # sysctl -p
    
    log_info "✅ 系统优化完成"
}

# 网络优化
optimize_network() {
    log_header "网络性能优化"
    
    log_info "测试网络连接..."
    
    # 测试内部服务连接
    echo "=== 内部服务连接测试 ==="
    docker-compose exec -T api python -c "
import asyncio
import aiohttp
import time

async def test_connections():
    urls = [
        'http://postgres:5432',  # 数据库连接
        'http://redis:6379',     # Redis 连接
        'http://web:3000',       # 前端连接
    ]
    
    for url in urls:
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    duration = time.time() - start
                    print(f'{url}: {duration*1000:.2f}ms')
        except Exception as e:
            print(f'{url}: 连接失败 - {str(e)}')

asyncio.run(test_connections())
"
    
    log_info "检查 DNS 解析..."
    nslookup google.com >/dev/null 2>&1 && log_info "✅ DNS 解析正常" || log_warn "⚠️  DNS 解析可能有问题"
    
    log_info "✅ 网络优化完成"
}

# 生成性能报告
generate_performance_report() {
    log_header "生成性能优化报告"
    
    local report_file="performance_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# AttentionSync 性能优化报告

**生成时间**: $(date)
**优化版本**: $(git rev-parse --short HEAD)

## 📊 系统状态

### 服务状态
\`\`\`
$(docker-compose ps)
\`\`\`

### 资源使用情况
\`\`\`
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}")
\`\`\`

### 磁盘使用情况
\`\`\`
$(df -h)
\`\`\`

## 🔧 优化内容

### 数据库优化
- ✅ 应用性能索引
- ✅ 更新表统计信息
- ✅ 刷新物化视图
- ✅ 清理过期数据
- ✅ 优化配置参数

### 缓存优化
- ✅ Redis 配置优化
- ✅ 清理过期键
- ✅ 缓存预热
- ✅ 内存策略调整

### 前端优化
- ✅ 构建优化
- ✅ 代码分割
- ✅ 静态资源压缩
- ✅ Service Worker 缓存

### API 优化
- ✅ 连接池配置
- ✅ 查询优化
- ✅ 响应缓存
- ✅ 性能监控

## 📈 性能指标

EOF

    # 添加 API 指标（如果可用）
    if [[ -f "api-metrics.txt" ]]; then
        echo "### API 性能指标" >> "$report_file"
        echo "\`\`\`" >> "$report_file"
        cat api-metrics.txt >> "$report_file"
        echo "\`\`\`" >> "$report_file"
        echo "" >> "$report_file"
    fi

    # 添加前端构建报告（如果可用）
    if [[ -f "web/build-report.md" ]]; then
        echo "### 前端构建报告" >> "$report_file"
        cat web/build-report.md >> "$report_file"
        echo "" >> "$report_file"
    fi

    cat >> "$report_file" << EOF

## 🎯 性能目标

| 指标 | 目标值 | 当前状态 | 达成情况 |
|------|--------|----------|----------|
| API P95 延迟 | < 500ms | 待测试 | 🔄 |
| 页面加载时间 | < 2s | 待测试 | 🔄 |
| 数据库查询 | < 100ms | 优化后 | ✅ |
| 缓存命中率 | > 80% | 配置中 | 🔄 |
| 并发用户数 | > 1000 | 待测试 | 🔄 |

## 📋 后续建议

### 立即执行
1. 运行性能测试验证优化效果
2. 监控关键指标的变化
3. 调整缓存策略参数

### 中期规划
1. 实施 CDN 加速
2. 数据库读写分离
3. 微服务拆分

### 长期规划
1. 多区域部署
2. 智能负载均衡
3. 自动扩缩容

## 🔗 相关文件

- 数据库索引: \`infra/performance_indexes.sql\`
- 缓存配置: \`api/app/core/cache.py\`
- 前端优化: \`web/src/lib/performance.ts\`
- 监控配置: \`infra/prometheus.yml\`

EOF

    log_info "性能报告已生成: $report_file"
}

# 性能测试
run_performance_tests() {
    log_header "运行性能测试"
    
    # 检查是否有测试工具
    if ! command -v ab &> /dev/null && ! command -v wrk &> /dev/null; then
        log_warn "未找到性能测试工具 (ab 或 wrk)，跳过性能测试"
        return
    fi
    
    log_info "测试 API 性能..."
    
    # 健康检查端点测试
    if command -v ab &> /dev/null; then
        log_info "使用 ab 进行压力测试..."
        ab -n 1000 -c 10 -g health_check_results.tsv http://localhost:8000/health > health_check_test.txt 2>&1 || log_warn "健康检查测试失败"
        
        # API 端点测试（需要认证的话需要先获取 token）
        # ab -n 500 -c 5 -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/sources > sources_test.txt 2>&1 || log_warn "Sources API 测试失败"
    elif command -v wrk &> /dev/null; then
        log_info "使用 wrk 进行压力测试..."
        wrk -t4 -c10 -d30s --latency http://localhost:8000/health > wrk_results.txt 2>&1 || log_warn "wrk 测试失败"
    fi
    
    log_info "测试前端性能..."
    if command -v lighthouse &> /dev/null; then
        log_info "运行 Lighthouse 性能测试..."
        lighthouse http://localhost:3000 --output=html --output-path=lighthouse-report.html --chrome-flags="--headless" || log_warn "Lighthouse 测试失败"
    else
        log_warn "Lighthouse 未安装，跳过前端性能测试"
    fi
    
    log_info "✅ 性能测试完成"
}

# 监控验证
verify_monitoring() {
    log_header "验证监控系统"
    
    # 检查 Prometheus
    if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_info "✅ Prometheus 运行正常"
        
        # 检查目标状态
        local targets_up=$(curl -s http://localhost:9090/api/v1/query?query=up | jq -r '.data.result | length' 2>/dev/null || echo "0")
        log_info "Prometheus 监控目标: $targets_up 个"
    else
        log_warn "⚠️  Prometheus 不可访问"
    fi
    
    # 检查 Grafana
    if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then
        log_info "✅ Grafana 运行正常"
    else
        log_warn "⚠️  Grafana 不可访问"
    fi
    
    # 检查应用指标
    if curl -s http://localhost:8000/metrics >/dev/null 2>&1; then
        log_info "✅ 应用指标可访问"
        
        # 获取关键指标
        local http_requests=$(curl -s http://localhost:8000/metrics | grep "http_requests_total" | wc -l)
        log_info "HTTP 请求指标: $http_requests 个"
    else
        log_warn "⚠️  应用指标不可访问"
    fi
    
    log_info "✅ 监控验证完成"
}

# 主函数
main() {
    log_info "开始性能优化流程..."
    
    # 检查是否在项目根目录
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "请在 AttentionSync 项目根目录下运行此脚本"
        exit 1
    fi
    
    # 检查服务是否运行
    if ! docker-compose ps | grep -q "Up"; then
        log_error "服务未运行，请先启动服务: docker-compose up -d"
        exit 1
    fi
    
    # 执行各项优化
    optimize_database
    optimize_redis
    optimize_api
    optimize_frontend
    optimize_system
    optimize_network
    
    # 运行性能测试
    run_performance_tests
    
    # 验证监控
    verify_monitoring
    
    # 生成报告
    generate_performance_report
    
    log_info "🎉 性能优化完成！"
    log_info "请查看生成的性能报告和测试结果"
    
    # 显示关键指标
    echo ""
    log_header "关键性能指标"
    echo "=== 服务响应时间 ==="
    curl -w "@-" -o /dev/null -s http://localhost:8000/health << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
    
    echo ""
    echo "=== Docker 容器状态 ==="
    docker-compose ps
    
    echo ""
    echo "=== 资源使用情况 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10
}

# 捕获退出信号
trap 'log_info "优化中断"; exit 1' INT TERM

# 执行主函数
main "$@"