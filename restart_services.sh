#!/bin/bash
#
# DOU+订单管理系统 - 服务重启脚本
#

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DOU+订单管理系统 - 重启服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 停止所有服务
bash /opt/douplus/stop_services.sh

echo ""
echo -e "${GREEN}等待3秒...${NC}"
sleep 3
echo ""

# 启动所有服务
bash /opt/douplus/start_services.sh
