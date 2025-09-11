#!/bin/bash

# AttentionSync 扩容部署脚本
# 支持水平扩容和服务管理

set -e

echo "🚀 AttentionSync 扩容部署管理"

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
    echo -e "${BLUE}[SCALE]${NC} $1"
}

# 默认参数
ACTION="status"
SERVICE=""
REPLICAS=1
COMPOSE_FILE="docker-compose.scale.yml"
ENVIRONMENT="production"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -r|--replicas)
            REPLICAS="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Actions:"
            echo "  status          Show current deployment status"
            echo "  scale           Scale services up/down"
            echo "  deploy          Deploy scaled configuration"
            echo "  restart         Restart services"
            echo "  stop            Stop services"
            echo "  logs            Show service logs"
            echo "  health          Check service health"
            echo ""
            echo "Options:"
            echo "  -a, --action ACTION     Action to perform (default: status)"
            echo "  -s, --service SERVICE   Target service name"
            echo "  -r, --replicas COUNT    Number of replicas (default: 1)"
            echo "  -f, --file FILE         Docker compose file (default: docker-compose.scale.yml)"
            echo "  -e, --environment ENV   Environment (default: production)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --action status"
            echo "  $0 --action scale --service api --replicas 5"
            echo "  $0 --action deploy"
            echo "  $0 --action health"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 检查 Docker 和 Docker Compose
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 统一使用 docker compose 命令
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
}

# 检查配置文件
check_config() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "配置文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    log_info "使用配置文件: $COMPOSE_FILE"
}

# 显示当前状态
show_status() {
    log_header "当前部署状态"
    
    echo "=== 服务状态 ==="
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "=== 资源使用情况 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo ""
    echo "=== 网络信息 ==="
    docker network ls --filter name=attentionsync
    
    echo ""
    echo "=== 存储卷 ==="
    docker volume ls --filter name=attentionsync
}

# 扩容服务
scale_service() {
    if [[ -z "$SERVICE" ]]; then
        log_error "请指定要扩容的服务名称"
        exit 1
    fi
    
    log_header "扩容服务: $SERVICE 到 $REPLICAS 个实例"
    
    case $SERVICE in
        api)
            log_info "扩容 API 服务..."
            # 动态创建多个 API 实例
            for ((i=1; i<=REPLICAS; i++)); do
                log_info "启动 API 实例 $i..."
                $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d api$i 2>/dev/null || log_warn "API$i 实例可能已存在"
            done
            ;;
        worker)
            log_info "扩容 Worker 服务..."
            for ((i=1; i<=REPLICAS; i++)); do
                log_info "启动 Worker 实例 $i..."
                $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d worker$i 2>/dev/null || log_warn "Worker$i 实例可能已存在"
            done
            ;;
        web)
            log_info "扩容 Web 服务..."
            for ((i=1; i<=REPLICAS; i++)); do
                log_info "启动 Web 实例 $i..."
                $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d web$i 2>/dev/null || log_warn "Web$i 实例可能已存在"
            done
            ;;
        *)
            log_info "扩容通用服务..."
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --scale "$SERVICE=$REPLICAS"
            ;;
    esac
    
    log_info "等待服务启动..."
    sleep 10
    
    log_info "验证服务状态..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
}

# 部署扩展配置
deploy_scaled() {
    log_header "部署扩展配置"
    
    # 检查环境变量
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        log_warn "环境配置文件不存在: .env.${ENVIRONMENT}"
        log_info "使用默认配置..."
    else
        log_info "加载环境配置: .env.${ENVIRONMENT}"
        export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
    fi
    
    # 拉取最新镜像
    log_info "拉取最新镜像..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" pull
    
    # 构建自定义镜像
    log_info "构建应用镜像..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" build --parallel
    
    # 启动基础服务
    log_info "启动数据库和缓存服务..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d postgres-master redis-master
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    wait_for_service "postgres-master" 5432 60
    wait_for_service "redis-master" 6379 30
    
    # 启动从库
    log_info "启动从库服务..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d postgres-slave1 postgres-slave2 redis-slave1 redis-slave2
    
    # 启动应用服务
    log_info "启动应用服务..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d api1 api2 api3 worker1 worker2 worker3 web1 web2
    
    # 启动负载均衡器
    log_info "启动负载均衡器..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d nginx
    
    # 健康检查
    log_info "执行健康检查..."
    check_health
    
    log_info "✅ 扩展部署完成！"
}

# 等待服务启动
wait_for_service() {
    local service=$1
    local port=$2
    local timeout=${3:-30}
    local count=0
    
    log_info "等待 $service:$port 启动..."
    
    while [[ $count -lt $timeout ]]; do
        if docker exec "attentionsync-$service" sh -c "nc -z localhost $port" 2>/dev/null; then
            log_info "$service 已启动"
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    log_error "$service 启动超时"
    return 1
}

# 健康检查
check_health() {
    log_header "服务健康检查"
    
    local services=("api1" "api2" "api3" "web1" "web2" "postgres-master" "redis-master" "nginx")
    local failed_services=()
    
    for service in "${services[@]}"; do
        log_info "检查 $service..."
        
        case $service in
            api*)
                if curl -f -s "http://localhost:8080/health" >/dev/null; then
                    echo "✅ $service - 健康"
                else
                    echo "❌ $service - 不健康"
                    failed_services+=("$service")
                fi
                ;;
            web*)
                if docker exec "attentionsync-$service" sh -c "curl -f -s http://localhost:3000" >/dev/null; then
                    echo "✅ $service - 健康"
                else
                    echo "❌ $service - 不健康"
                    failed_services+=("$service")
                fi
                ;;
            postgres-master)
                if docker exec "attentionsync-$service" pg_isready -U attentionsync >/dev/null; then
                    echo "✅ $service - 健康"
                else
                    echo "❌ $service - 不健康"
                    failed_services+=("$service")
                fi
                ;;
            redis-master)
                if docker exec "attentionsync-$service" redis-cli ping >/dev/null; then
                    echo "✅ $service - 健康"
                else
                    echo "❌ $service - 不健康"
                    failed_services+=("$service")
                fi
                ;;
            nginx)
                if curl -f -s "http://localhost:8080/health" >/dev/null; then
                    echo "✅ $service - 健康"
                else
                    echo "❌ $service - 不健康"
                    failed_services+=("$service")
                fi
                ;;
        esac
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_info "✅ 所有服务健康"
        return 0
    else
        log_error "❌ 以下服务不健康: ${failed_services[*]}"
        return 1
    fi
}

# 重启服务
restart_services() {
    if [[ -n "$SERVICE" ]]; then
        log_header "重启服务: $SERVICE"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" restart "$SERVICE"
    else
        log_header "重启所有服务"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" restart
    fi
}

# 停止服务
stop_services() {
    if [[ -n "$SERVICE" ]]; then
        log_header "停止服务: $SERVICE"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" stop "$SERVICE"
    else
        log_header "停止所有服务"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" stop
    fi
}

# 查看日志
show_logs() {
    if [[ -n "$SERVICE" ]]; then
        log_header "查看服务日志: $SERVICE"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs -f --tail=100 "$SERVICE"
    else
        log_header "查看所有服务日志"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs -f --tail=100
    fi
}

# 性能监控
performance_monitor() {
    log_header "性能监控"
    
    echo "=== CPU 和内存使用情况 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -20
    
    echo ""
    echo "=== 网络流量 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.NetIO}}\t{{.BlockIO}}" | head -20
    
    echo ""
    echo "=== 磁盘使用情况 ==="
    df -h | grep -E "(Filesystem|/dev/)"
    
    echo ""
    echo "=== Docker 系统信息 ==="
    docker system df
}

# 自动扩容建议
scaling_recommendations() {
    log_header "自动扩容建议"
    
    # 检查 CPU 使用率
    local high_cpu_containers=$(docker stats --no-stream --format "{{.Container}}\t{{.CPUPerc}}" | awk -F'\t' '$2 > 80 {print $1}')
    
    if [[ -n "$high_cpu_containers" ]]; then
        log_warn "以下容器 CPU 使用率过高:"
        echo "$high_cpu_containers"
        log_info "建议扩容相关服务"
    fi
    
    # 检查内存使用率
    local high_mem_containers=$(docker stats --no-stream --format "{{.Container}}\t{{.MemPerc}}" | awk -F'\t' '$2 > 85 {print $1}')
    
    if [[ -n "$high_mem_containers" ]]; then
        log_warn "以下容器内存使用率过高:"
        echo "$high_mem_containers"
        log_info "建议增加内存或扩容服务"
    fi
    
    # 检查负载均衡状态
    if curl -s "http://localhost:8080/nginx_status" | grep -q "Active connections"; then
        local active_connections=$(curl -s "http://localhost:8080/nginx_status" | grep "Active connections" | awk '{print $3}')
        log_info "Nginx 活跃连接数: $active_connections"
        
        if [[ $active_connections -gt 500 ]]; then
            log_warn "连接数较高，建议扩容 API 服务"
        fi
    fi
}

# 主函数
main() {
    log_info "开始扩容部署管理..."
    
    # 检查依赖
    check_dependencies
    
    # 检查配置
    check_config
    
    # 执行操作
    case $ACTION in
        status)
            show_status
            ;;
        scale)
            scale_service
            ;;
        deploy)
            deploy_scaled
            ;;
        restart)
            restart_services
            ;;
        stop)
            stop_services
            ;;
        logs)
            show_logs
            ;;
        health)
            check_health
            ;;
        monitor)
            performance_monitor
            ;;
        recommend)
            scaling_recommendations
            ;;
        *)
            log_error "未知操作: $ACTION"
            exit 1
            ;;
    esac
    
    log_info "✅ 操作完成！"
}

# 捕获退出信号
trap 'log_info "清理中..."; exit 0' INT TERM

# 执行主函数
main "$@"