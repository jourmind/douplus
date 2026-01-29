#!/bin/bash
# 重启Celery服务

cd /opt/douplus/douplus-sync-python

echo "停止Celery服务..."
pkill -f "celery -A celery_app"
sleep 2

echo "启动Celery Worker..."
nohup celery -A celery_app worker --loglevel=info > logs/celery_worker.log 2>&1 &

sleep 2

echo "启动Celery Beat..."
celery -A celery_app beat --loglevel=info --logfile=logs/beat.log --pidfile=logs/beat.pid --detach

sleep 2

echo "检查Celery服务状态..."
ps aux | grep celery | grep -v grep

echo "Celery服务重启完成！"
