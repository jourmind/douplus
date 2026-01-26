#!/bin/bash

# DOU+ Python同步服务启动脚本

# 添加Python用户bin目录到PATH
export PATH="$HOME/.local/bin:$PATH"

cd /opt/douplus/douplus-sync-python

case "$1" in
    install)
        echo "安装Python依赖..."
        pip3 install -r requirements.txt
        echo "依赖安装完成"
        ;;
    
    worker)
        echo "启动Celery Worker..."
        celery -A celery_app worker --loglevel=info --logfile=logs/worker.log &
        echo "Worker已启动"
        ;;
    
    beat)
        echo "启动Celery Beat (定时任务)..."
        celery -A celery_app beat --loglevel=info --logfile=logs/beat.log &
        echo "Beat已启动"
        ;;
    
    api)
        echo "启动API服务..."
        nohup python3 api_server.py > logs/api.log 2>&1 &
        echo $! > logs/api.pid
        echo "API服务已启动"
        ;;
    
    start)
        echo "启动完整服务..."
        # 启动Worker
        celery -A celery_app worker --loglevel=info --logfile=logs/worker.log --pidfile=logs/worker.pid --detach
        # 启动Beat
        celery -A celery_app beat --loglevel=info --logfile=logs/beat.log --pidfile=logs/beat.pid --detach
        # 启动API服务
        nohup python3 api_server.py > logs/api.log 2>&1 &
        echo $! > logs/api.pid
        echo "所有服务已启动"
        ;;
    
    stop)
        echo "停止所有服务..."
        pkill -f "celery.*celery_app"
        if [ -f logs/api.pid ]; then
            kill $(cat logs/api.pid) 2>/dev/null
            rm logs/api.pid
        fi
        pkill -f "python3 api_server.py"
        echo "所有服务已停止"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        echo "检查服务状态..."
        echo "=== Celery Worker/Beat ==="
        ps aux | grep "celery.*celery_app" | grep -v grep
        echo ""
        echo "=== API Server ==="
        ps aux | grep "python3 api_server.py" | grep -v grep
        ;;
    
    logs)
        echo "查看日志..."
        tail -f logs/*.log
        ;;
    
    *)
        echo "Usage: $0 {install|start|stop|restart|api|worker|beat|status|logs}"
        exit 1
        ;;
esac

