#!/bin/bash
# =========================================
# DOU+后端服务启动脚本
# =========================================

# 项目根目录
PROJECT_DIR="/opt/douplus"
SERVER_DIR="$PROJECT_DIR/douplus-server"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p $LOG_DIR

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

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
            echo "Service is already running with PID: $PID"
            return 1
        fi
    fi
    
    echo "Starting DOU+ Server..."
    nohup java -jar \
        -Xms512m -Xmx1024m \
        -XX:+UseG1GC \
        -XX:MaxGCPauseMillis=200 \
        -Dfile.encoding=UTF-8 \
        -Duser.timezone=Asia/Shanghai \
        $JAR_PATH \
        > "$LOG_DIR/stdout.log" 2>&1 &
    
    echo $! > $PID_FILE
    echo "Service started with PID: $(cat $PID_FILE)"
}

# 停止函数
stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping DOU+ Server (PID: $PID)..."
            kill $PID
            sleep 3
            
            # 强制停止
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force stopping..."
                kill -9 $PID
            fi
            
            rm -f $PID_FILE
            echo "Service stopped."
        else
            echo "Process not found, cleaning up PID file..."
            rm -f $PID_FILE
        fi
    else
        echo "PID file not found. Service may not be running."
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
            echo "Service is running with PID: $PID"
            return 0
        else
            echo "Service is not running (stale PID file)"
            return 1
        fi
    else
        echo "Service is not running"
        return 1
    fi
}

# 构建函数
build() {
    echo "Building DOU+ Server..."
    cd $SERVER_DIR
    mvn clean package -DskipTests
    echo "Build completed."
}

# 使用说明
usage() {
    echo "Usage: $0 {start|stop|restart|status|build}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the service"
    echo "  stop    - Stop the service"
    echo "  restart - Restart the service"
    echo "  status  - Check service status"
    echo "  build   - Build the JAR package"
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
    *)
        usage
        exit 1
        ;;
esac
