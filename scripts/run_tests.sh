#!/bin/bash

# AttentionSync 测试运行脚本
# 支持不同级别的测试和报告生成

set -e

echo "🧪 AttentionSync 测试套件"

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
    echo -e "${BLUE}[TEST]${NC} $1"
}

# 默认参数
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
PARALLEL=false
REPORT_FORMAT="term"
OUTPUT_DIR="test-reports"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -f|--format)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --type TYPE      Test type: unit, integration, e2e, all (default: all)"
            echo "  -c, --coverage       Generate coverage report"
            echo "  -v, --verbose        Verbose output"
            echo "  -p, --parallel       Run tests in parallel"
            echo "  -f, --format FORMAT  Report format: term, html, xml (default: term)"
            echo "  -o, --output DIR     Output directory for reports (default: test-reports)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 检查依赖
check_dependencies() {
    log_info "检查测试依赖..."
    
    if ! command -v pytest &> /dev/null; then
        log_error "pytest 未安装"
        exit 1
    fi
    
    if [[ "$COVERAGE" == true ]] && ! command -v pytest-cov &> /dev/null; then
        log_error "pytest-cov 未安装"
        exit 1
    fi
    
    if [[ "$PARALLEL" == true ]] && ! python -c "import pytest_xdist" &> /dev/null; then
        log_warn "pytest-xdist 未安装，将使用单线程运行"
        PARALLEL=false
    fi
}

# 设置测试环境
setup_test_environment() {
    log_info "设置测试环境..."
    
    export ENVIRONMENT=testing
    export DATABASE_URL=sqlite:///:memory:
    export REDIS_URL=redis://localhost:6379/15
    export SECRET_KEY=test-secret-key-for-testing-only
    export JWT_SECRET=test-jwt-secret-for-testing-only
    
    # 创建输出目录
    mkdir -p "$OUTPUT_DIR"
    
    # 清理之前的测试数据
    if command -v redis-cli &> /dev/null; then
        redis-cli -n 15 FLUSHDB &> /dev/null || log_warn "无法清理 Redis 测试数据库"
    fi
}

# 构建 pytest 命令
build_pytest_command() {
    local cmd="pytest"
    
    # 基础参数
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd -v"
    else
        cmd="$cmd -q"
    fi
    
    # 并行执行
    if [[ "$PARALLEL" == true ]]; then
        local cpu_count=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "4")
        cmd="$cmd -n $cpu_count"
    fi
    
    # 覆盖率
    if [[ "$COVERAGE" == true ]]; then
        cmd="$cmd --cov=app --cov-report=term-missing"
        
        case $REPORT_FORMAT in
            html)
                cmd="$cmd --cov-report=html:$OUTPUT_DIR/coverage-html"
                ;;
            xml)
                cmd="$cmd --cov-report=xml:$OUTPUT_DIR/coverage.xml"
                ;;
        esac
    fi
    
    # 测试结果报告
    case $REPORT_FORMAT in
        html)
            cmd="$cmd --html=$OUTPUT_DIR/report.html --self-contained-html"
            ;;
        xml)
            cmd="$cmd --junitxml=$OUTPUT_DIR/junit.xml"
            ;;
    esac
    
    # 测试类型
    case $TEST_TYPE in
        unit)
            cmd="$cmd -m 'not integration and not e2e'"
            ;;
        integration)
            cmd="$cmd -m integration"
            ;;
        e2e)
            cmd="$cmd -m e2e"
            ;;
        all)
            # 运行所有测试
            ;;
        *)
            log_error "无效的测试类型: $TEST_TYPE"
            exit 1
            ;;
    esac
    
    echo "$cmd"
}

# 运行单元测试
run_unit_tests() {
    log_header "运行单元测试"
    
    local cmd=$(build_pytest_command)
    if [[ "$TEST_TYPE" != "unit" ]]; then
        cmd="$cmd -m 'not integration and not e2e'"
    fi
    
    cd api
    eval "$cmd tests/test_core/ tests/test_utils/"
    cd ..
}

# 运行集成测试
run_integration_tests() {
    log_header "运行集成测试"
    
    # 检查 Redis 连接
    if ! redis-cli ping &> /dev/null; then
        log_warn "Redis 未运行，跳过需要 Redis 的集成测试"
        return 0
    fi
    
    local cmd=$(build_pytest_command)
    if [[ "$TEST_TYPE" != "integration" ]]; then
        cmd="$cmd -m integration"
    fi
    
    cd api
    eval "$cmd tests/test_services/ tests/test_routers/"
    cd ..
}

# 运行端到端测试
run_e2e_tests() {
    log_header "运行端到端测试"
    
    # 启动测试服务
    log_info "启动测试服务..."
    docker-compose -f docker-compose.test.yml up -d --build
    
    # 等待服务启动
    sleep 10
    
    # 健康检查
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            break
        fi
        log_info "等待服务启动... ($retries)"
        sleep 2
        ((retries--))
    done
    
    if [[ $retries -eq 0 ]]; then
        log_error "测试服务启动失败"
        docker-compose -f docker-compose.test.yml down
        exit 1
    fi
    
    local cmd=$(build_pytest_command)
    if [[ "$TEST_TYPE" != "e2e" ]]; then
        cmd="$cmd -m e2e"
    fi
    
    cd api
    eval "$cmd tests/test_e2e/"
    local test_result=$?
    cd ..
    
    # 清理测试服务
    log_info "清理测试服务..."
    docker-compose -f docker-compose.test.yml down -v
    
    return $test_result
}

# 运行代码质量检查
run_quality_checks() {
    log_header "运行代码质量检查"
    
    cd api
    
    # 类型检查
    if command -v mypy &> /dev/null; then
        log_info "运行类型检查..."
        mypy app/ --ignore-missing-imports --no-strict-optional
    else
        log_warn "mypy 未安装，跳过类型检查"
    fi
    
    # 代码风格检查
    if command -v flake8 &> /dev/null; then
        log_info "运行代码风格检查..."
        flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
    else
        log_warn "flake8 未安装，跳过代码风格检查"
    fi
    
    # 安全检查
    if command -v bandit &> /dev/null; then
        log_info "运行安全检查..."
        bandit -r app/ -f json -o "$OUTPUT_DIR/bandit-report.json" || log_warn "发现安全问题"
    else
        log_warn "bandit 未安装，跳过安全检查"
    fi
    
    cd ..
}

# 生成测试报告
generate_report() {
    log_header "生成测试报告"
    
    local report_file="$OUTPUT_DIR/test-summary.md"
    
    cat > "$report_file" << EOF
# AttentionSync 测试报告

**生成时间**: $(date)
**测试类型**: $TEST_TYPE
**覆盖率**: $([ "$COVERAGE" = true ] && echo "启用" || echo "禁用")

## 测试结果

EOF

    # 添加覆盖率信息
    if [[ "$COVERAGE" == true ]] && [[ -f "$OUTPUT_DIR/coverage.xml" ]]; then
        echo "### 代码覆盖率" >> "$report_file"
        echo "" >> "$report_file"
        # 解析覆盖率 XML（简化版本）
        if command -v xmllint &> /dev/null; then
            local coverage=$(xmllint --xpath "string(/coverage/@line-rate)" "$OUTPUT_DIR/coverage.xml" 2>/dev/null)
            if [[ -n "$coverage" ]]; then
                local percentage=$(echo "$coverage * 100" | bc -l 2>/dev/null | cut -d. -f1)
                echo "- 行覆盖率: ${percentage}%" >> "$report_file"
            fi
        fi
        echo "" >> "$report_file"
    fi
    
    # 添加文件链接
    echo "## 详细报告" >> "$report_file"
    echo "" >> "$report_file"
    
    if [[ -f "$OUTPUT_DIR/report.html" ]]; then
        echo "- [HTML 测试报告](report.html)" >> "$report_file"
    fi
    
    if [[ -f "$OUTPUT_DIR/coverage-html/index.html" ]]; then
        echo "- [HTML 覆盖率报告](coverage-html/index.html)" >> "$report_file"
    fi
    
    if [[ -f "$OUTPUT_DIR/bandit-report.json" ]]; then
        echo "- [安全检查报告](bandit-report.json)" >> "$report_file"
    fi
    
    log_info "测试报告已生成: $report_file"
}

# 主函数
main() {
    log_info "开始测试流程..."
    
    # 检查依赖
    check_dependencies
    
    # 设置环境
    setup_test_environment
    
    # 根据测试类型运行测试
    case $TEST_TYPE in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        all)
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            ;;
    esac
    
    # 运行代码质量检查
    if [[ "$TEST_TYPE" == "all" ]] || [[ "$TEST_TYPE" == "unit" ]]; then
        run_quality_checks
    fi
    
    # 生成报告
    generate_report
    
    log_info "✅ 测试完成！"
    log_info "查看报告: $OUTPUT_DIR/"
}

# 捕获退出信号进行清理
trap 'log_info "清理测试环境..."; docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true' EXIT

# 执行主函数
main "$@"