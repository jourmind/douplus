#!/bin/bash
#
# DOU+订单管理系统 - 服务停止脚本
#

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DOU+订单管理系统 - 停止服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 停止 Flask API
echo -e "${YELLOW}停止 Flask API...${NC}"
if pgrep -f "python3 api_server.py" > /dev/null; then
    pkill -f "python3 api_server.py"
    sleep 1
    if pgrep -f "python3 api_server.py" > /dev/null; then
        echo -e "${RED}✗ Flask API 停止失败${NC}"
    else
        echo -e "${GREEN}✓ Flask API 已停止${NC}"
    fi
else
    echo -e "${YELLOW}  Flask API 未运行${NC}"
fi

# 停止 Celery Worker
echo -e "${YELLOW}停止 Celery Worker...${NC}"
if pgrep -f "celery -A celery_app worker" > /dev/null; then
    pkill -f "celery -A celery_app worker"
    sleep 2
    if pgrep -f "celery -A celery_app worker" > /dev/null; then
        echo -e "${RED}✗ Celery Worker 停止失败${NC}"
    else
        echo -e "${GREEN}✓ Celery Worker 已停止${NC}"
    fi
else
    echo -e "${YELLOW}  Celery Worker 未运行${NC}"
fi

# 停止 Celery Beat
echo -e "${YELLOW}停止 Celery Beat...${NC}"
if pgrep -f "celery -A celery_app beat" > /dev/null; then
    pkill -f "celery -A celery_app beat"
    sleep 1
    if pgrep -f "celery -A celery_app beat" > /dev/null; then
        echo -e "${RED}✗ Celery Beat 停止失败${NC}"
    else
        echo -e "${GREEN}✓ Celery Beat 已停止${NC}"
    fi
else
    echo -e "${YELLOW}  Celery Beat 未运行${NC}"
fi

echo ""
echo -e "${GREEN}✓ 所有服务已停止${NC}"
echo ""
