#!/bin/bash
# =========================================
# DOU+后端服务启动脚本
# 用法: ./start-server.sh {start|stop|restart|status|build}
# =========================================

# 项目根目录
PROJECT_DIR="/opt/douplus"
SERVER_DIR="$PROJECT_DIR/douplus-server"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p $LOG_DIR

# 加载环境变量
load_env() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo "加载环境变量配置..."
        set -a
        source "$PROJECT_DIR/.env"
        set +a
        echo "✓ MYSQL_PASSWORD: $([[ -n $MYSQL_PASSWORD ]] && echo '已配置' || echo '未配置')"
        echo "✓ JWT_SECRET: $([[ -n $JWT_SECRET ]] && echo '已配置' || echo '未配置')"
        echo "✓ DOUYIN_APP_ID: $([[ -n $DOUYIN_APP_ID ]] && echo '已配置' || echo '未配置')"
        echo "✓ DOUYIN_OAUTH_CALLBACK: $([[ -n $DOUYIN_OAUTH_CALLBACK ]] && echo '已配置' || echo '未配置')"
    else
        echo "警告: 未找到 $PROJECT_DIR/.env 文件"
        echo "请复制 .env.example 并配置环境变量"
        exit 1
    fi
}

# JAR包名称
JAR_NAME="douplus-server-1.0.0.jar"
JAR_PATH="$SERVER_DIR/target/$JAR_NAME"

# PID文件
PID_FILE="$PROJECT_DIR/douplus.pid"

# 启动函数
start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "服务已在运行，PID: $PID"
            return 1
        fi
    fi
    
    # 检查JAR包是否存在
    if [ ! -f "$JAR_PATH" ]; then
        echo "错误: 未找到 $JAR_PATH"
        echo "请先运行: $0 build"
        exit 1
    fi
    
    # 加载环境变量
    load_env
    
    echo ""
    echo "启动 DOU+ Server..."
    nohup java -jar \
        -Xms256m -Xmx512m \
        -XX:+UseG1GC \
        -XX:MaxGCPauseMillis=200 \
        -Dfile.encoding=UTF-8 \
        -Duser.timezone=Asia/Shanghai \
        $JAR_PATH \
        > "$LOG_DIR/stdout.log" 2>&1 &
    
    echo $! > $PID_FILE
    sleep 3
    
    # 检查是否启动成功
    if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
        echo "✓ 服务启动成功，PID: $(cat $PID_FILE)"
        echo "日志文件: $LOG_DIR/stdout.log"
    else
        echo "✗ 服务启动失败，请检查日志"
        tail -20 "$LOG_DIR/stdout.log"
        exit 1
    fi
}

# 停止函数
stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "停止 DOU+ Server (PID: $PID)..."
            kill $PID
            sleep 3
            
            # 强制停止
            if ps -p $PID > /dev/null 2>&1; then
                echo "强制停止..."
                kill -9 $PID
            fi
            
            rm -f $PID_FILE
            echo "✓ 服务已停止"
        else
            echo "进程不存在，清理PID文件..."
            rm -f $PID_FILE
        fi
    else
        echo "PID文件不存在，服务可能未运行"
        # 尝试通过进程名查找并停止
        pkill -f 'douplus-server' 2>/dev/null && echo "✓ 已停止残留进程"
    fi
}

# 重启函数
restart() {
    stop
    sleep 2
    start
}

# 状态函数
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "✓ 服务运行中，PID: $PID"
            echo "内存使用: $(ps -p $PID -o rss= | awk '{print int($1/1024)"MB"}')"
            return 0
        else
            echo "✗ 服务未运行 (PID文件已过期)"
            return 1
        fi
    else
        echo "✗ 服务未运行"
        return 1
    fi
}

# 构建函数
build() {
    echo "构建 DOU+ Server..."
    cd $SERVER_DIR
    mvn clean package -DskipTests
    if [ $? -eq 0 ]; then
        echo "✓ 构建完成"
    else
        echo "✗ 构建失败"
        exit 1
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_DIR/stdout.log" ]; then
        tail -f "$LOG_DIR/stdout.log"
    else
        echo "日志文件不存在"
    fi
}

# 使用说明
usage() {
    echo "=========================================="
    echo "DOU+ 后端服务管理脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 {start|stop|restart|status|build|logs}"
    echo ""
    echo "命令:"
    echo "  start   - 启动服务"
    echo "  stop    - 停止服务"
    echo "  restart - 重启服务"
    echo "  status  - 查看服务状态"
    echo "  build   - 构建JAR包"
    echo "  logs    - 查看实时日志"
    echo ""
    echo "配置文件: $PROJECT_DIR/.env"
}

# 主逻辑
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    build)
        build
        ;;
    logs)
        logs
        ;;
    *)
        usage
        exit 1
        ;;
esac
