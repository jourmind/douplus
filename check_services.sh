#!/bin/bash
#
# DOU+订单管理系统 - 服务状态检查脚本
#

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DOU+订单管理系统 - 服务状态${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Flask API
if pgrep -f "python3 api_server.py" > /dev/null; then
    PID=$(pgrep -f "python3 api_server.py")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/auth/info 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
        echo -e "Flask API:      ${GREEN}✓ 运行中${NC} (PID: $PID, HTTP: $HTTP_CODE)"
    else
        echo -e "Flask API:      ${YELLOW}⚠ 运行但响应异常${NC} (PID: $PID, HTTP: $HTTP_CODE)"
    fi
else
    echo -e "Flask API:      ${RED}✗ 未运行${NC}"
fi

# Celery Worker
WORKER_COUNT=$(pgrep -f "celery -A celery_app worker" | wc -l)
if [ "$WORKER_COUNT" -ge 1 ]; then
    echo -e "Celery Worker:  ${GREEN}✓ 运行中${NC} ($WORKER_COUNT 个进程)"
else
    echo -e "Celery Worker:  ${RED}✗ 未运行${NC}"
fi

# Celery Beat
if pgrep -f "celery -A celery_app beat" > /dev/null; then
    PID=$(pgrep -f "celery -A celery_app beat")
    echo -e "Celery Beat:    ${GREEN}✓ 运行中${NC} (PID: $PID)"
else
    echo -e "Celery Beat:    ${RED}✗ 未运行${NC}"
fi

echo ""
echo -e "${BLUE}提示：${NC}"
echo "  启动服务: bash /opt/douplus/start_services.sh"
echo "  停止服务: bash /opt/douplus/stop_services.sh"
echo ""
