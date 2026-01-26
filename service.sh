#!/bin/bash
# DOU+ 系统服务管理脚本

case "$1" in
    start)
        echo "启动DOU+服务..."
        cd /opt/douplus/douplus-sync-python && ./manage.sh start
        echo "✅ Python服务已启动"
        ;;
    
    stop)
        echo "停止DOU+服务..."
        cd /opt/douplus/douplus-sync-python && ./manage.sh stop
        echo "✅ Python服务已停止"
        ;;
    
    restart)
        echo "重启DOU+服务..."
        cd /opt/douplus/douplus-sync-python && ./manage.sh restart
        echo "✅ Python服务已重启"
        ;;
    
    status)
        echo "==================================="
        echo "DOU+ Python服务状态"
        echo "==================================="
        cd /opt/douplus/douplus-sync-python && ./manage.sh status
        echo ""
        echo "==================================="
        echo "测试API接口"
        echo "==================================="
        echo "健康检查:"
        curl -s http://127.0.0.1:5000/health | python3 -m json.tool 2>/dev/null || echo "❌ API服务未响应"
        echo ""
        echo "同步状态:"
        curl -s http://127.0.0.1:5000/api/douplus/task/sync-status | python3 -m json.tool 2>/dev/null || echo "❌ API服务未响应"
        ;;
    
    logs)
        echo "查看日志（Ctrl+C退出）..."
        cd /opt/douplus/douplus-sync-python && tail -f logs/*.log
        ;;
    
    test)
        echo "==================================="
        echo "测试API接口"
        echo "==================================="
        echo ""
        echo "1. 健康检查:"
        curl -s http://127.0.0.1:5000/health | python3 -m json.tool
        echo ""
        echo "2. 同步状态查询:"
        curl -s http://127.0.0.1:5000/api/douplus/task/sync-status | python3 -m json.tool
        echo ""
        echo "3. 通过Nginx访问（HTTP）:"
        curl -s http://42.194.181.242/api/douplus/task/sync-status 2>&1 | head -5
        ;;
    
    *)
        echo "DOU+ Python服务管理"
        echo ""
        echo "用法: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动所有Python服务（API + Worker + Beat）"
        echo "  stop    - 停止所有Python服务"
        echo "  restart - 重启所有Python服务"
        echo "  status  - 查看服务运行状态"
        echo "  logs    - 实时查看日志"
        echo "  test    - 测试API接口"
        echo ""
        echo "前端访问地址: https://42.194.181.242"
        exit 1
        ;;
esac
