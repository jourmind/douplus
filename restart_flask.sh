#!/bin/bash
# Flask后端服务重启脚本

echo "=========================================="
echo "重启Flask后端服务"
echo "=========================================="
echo ""

# 查找Flask进程
FLASK_PID=$(lsof -i :5000 2>/dev/null | grep LISTEN | awk '{print $2}')

if [ -z "$FLASK_PID" ]; then
    echo "❌ 未找到运行在5000端口的Flask服务"
    exit 1
fi

echo "📍 找到Flask进程: PID=$FLASK_PID"
echo ""

# 查看进程信息
echo "进程详情："
ps aux | grep $FLASK_PID | grep -v grep
echo ""

# 杀掉进程
echo "正在停止服务..."
kill $FLASK_PID
sleep 2

# 检查是否成功停止
if ps -p $FLASK_PID > /dev/null 2>&1; then
    echo "⚠️  进程仍在运行，尝试强制终止..."
    kill -9 $FLASK_PID
    sleep 1
fi

echo "✅ Flask服务已停止"
echo ""

# 重新启动
echo "正在启动Flask服务..."
cd /opt/douplus/douplus-sync-python

# 后台启动Flask
nohup python3 -m flask run --host=0.0.0.0 --port=5000 > logs/flask.log 2>&1 &
NEW_PID=$!

sleep 2

# 验证启动
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ Flask服务已启动"
    echo "   PID: $NEW_PID"
    echo "   日志: /opt/douplus/douplus-sync-python/logs/flask.log"
    echo ""
    echo "查看实时日志："
    echo "  tail -f /opt/douplus/douplus-sync-python/logs/flask.log"
else
    echo "❌ Flask服务启动失败"
    echo "查看错误日志："
    echo "  cat /opt/douplus/douplus-sync-python/logs/flask.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 重启完成"
echo "=========================================="
