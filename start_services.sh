#!/bin/bash
#
# DOU+订单管理系统 - 服务启动脚本
# 
# 功能：
# 1. 检查并启动所有必需服务
# 2. 验证服务健康状态
# 3. 提供失败诊断信息
#
# 使用方法：
#   bash /opt/douplus/start_services.sh
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/opt/douplus/douplus-sync-python"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DOU+订单管理系统 - 服务启动${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

#
# 1. 检查并启动 Flask API 服务
#
echo -e "${YELLOW}[1/3] 检查 Flask API 服务...${NC}"

if pgrep -f "python3 api_server.py" > /dev/null; then
    PID=$(pgrep -f "python3 api_server.py")
    echo -e "${GREEN}✓ Flask API 已运行 (PID: $PID)${NC}"
else
    echo -e "${YELLOW}  启动 Flask API 服务...${NC}"
    cd "$PROJECT_DIR"
    nohup python3 api_server.py > "$LOG_DIR/api_server.log" 2>&1 &
    sleep 3
    
    if pgrep -f "python3 api_server.py" > /dev/null; then
        PID=$(pgrep -f "python3 api_server.py")
        echo -e "${GREEN}✓ Flask API 启动成功 (PID: $PID)${NC}"
    else
        echo -e "${RED}✗ Flask API 启动失败${NC}"
        echo -e "${YELLOW}诊断信息：${NC}"
        echo "  1. 检查端口5000是否被占用: sudo netstat -tlnp | grep 5000"
        echo "  2. 查看错误日志: tail -50 $LOG_DIR/api_server.log"
        echo "  3. 检查Python环境: python3 --version"
        echo "  4. 检查依赖安装: pip3 list | grep -E '(flask|sqlalchemy)'"
        exit 1
    fi
fi

# 验证API健康
sleep 1
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/auth/info 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API 响应正常 (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠ API 响应异常 (HTTP $HTTP_CODE)，但服务可能正在启动中${NC}"
fi

echo ""

#
# 2. 检查并启动 Celery Worker
#
echo -e "${YELLOW}[2/3] 检查 Celery Worker...${NC}"

WORKER_COUNT=$(pgrep -f "celery -A celery_app worker" | wc -l)
if [ "$WORKER_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✓ Celery Worker 已运行 ($WORKER_COUNT 个进程)${NC}"
else
    echo -e "${YELLOW}  启动 Celery Worker...${NC}"
    cd "$PROJECT_DIR"
    nohup celery -A celery_app worker --loglevel=info > "$LOG_DIR/celery_worker.log" 2>&1 &
    sleep 5
    
    WORKER_COUNT=$(pgrep -f "celery -A celery_app worker" | wc -l)
    if [ "$WORKER_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✓ Celery Worker 启动成功 ($WORKER_COUNT 个进程)${NC}"
        
        # 检查Worker是否ready
        sleep 2
        if grep -q "ready" "$LOG_DIR/celery_worker.log" 2>/dev/null; then
            echo -e "${GREEN}✓ Celery Worker 已就绪${NC}"
        else
            echo -e "${YELLOW}⚠ Celery Worker 正在初始化...${NC}"
        fi
    else
        echo -e "${RED}✗ Celery Worker 启动失败${NC}"
        echo -e "${YELLOW}诊断信息：${NC}"
        echo "  1. 检查Redis连接: redis-cli ping"
        echo "  2. 查看错误日志: tail -50 $LOG_DIR/celery_worker.log"
        echo "  3. 检查Celery安装: pip3 show celery"
        echo "  4. 手动启动测试: cd $PROJECT_DIR && celery -A celery_app worker --loglevel=info"
        exit 1
    fi
fi

echo ""

#
# 3. 检查并启动 Celery Beat (定时任务调度器)
#
echo -e "${YELLOW}[3/3] 检查 Celery Beat...${NC}"

if pgrep -f "celery -A celery_app beat" > /dev/null; then
    PID=$(pgrep -f "celery -A celery_app beat")
    echo -e "${GREEN}✓ Celery Beat 已运行 (PID: $PID)${NC}"
else
    echo -e "${YELLOW}  启动 Celery Beat...${NC}"
    cd "$PROJECT_DIR"
    
    # 清理旧的PID文件（如果存在）
    rm -f "$LOG_DIR/beat.pid"
    
    celery -A celery_app beat --loglevel=info --logfile="$LOG_DIR/beat.log" --pidfile="$LOG_DIR/beat.pid" --detach
    sleep 3
    
    if pgrep -f "celery -A celery_app beat" > /dev/null; then
        PID=$(pgrep -f "celery -A celery_app beat")
        echo -e "${GREEN}✓ Celery Beat 启动成功 (PID: $PID)${NC}"
    else
        echo -e "${RED}✗ Celery Beat 启动失败${NC}"
        echo -e "${YELLOW}诊断信息：${NC}"
        echo "  1. 查看错误日志: tail -50 $LOG_DIR/beat.log"
        echo "  2. 检查PID文件: ls -lh $LOG_DIR/beat.pid"
        echo "  3. 手动启动测试: cd $PROJECT_DIR && celery -A celery_app beat --loglevel=info"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 所有服务启动完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 显示服务状态摘要
echo -e "${BLUE}服务状态摘要：${NC}"
echo "----------------------------------------"

# Flask API
FLASK_PID=$(pgrep -f "python3 api_server.py" | head -1)
echo -e "Flask API Server:  ${GREEN}运行中${NC} (PID: $FLASK_PID)"
echo "  └─ 访问地址: http://127.0.0.1:5000"
echo "  └─ 日志文件: $LOG_DIR/api_server.log"

# Celery Worker
WORKER_PIDS=$(pgrep -f "celery -A celery_app worker" | tr '\n' ' ')
WORKER_COUNT=$(echo $WORKER_PIDS | wc -w)
echo -e "Celery Worker:     ${GREEN}运行中${NC} ($WORKER_COUNT 个进程)"
echo "  └─ 日志文件: $LOG_DIR/celery_worker.log"

# Celery Beat
BEAT_PID=$(pgrep -f "celery -A celery_app beat" | head -1)
echo -e "Celery Beat:       ${GREEN}运行中${NC} (PID: $BEAT_PID)"
echo "  └─ 日志文件: $LOG_DIR/beat.log"

echo "----------------------------------------"
echo ""

# 定时任务列表
echo -e "${BLUE}定时任务列表：${NC}"
echo "  • 每5分钟增量同步订单 (1,6,11,16...)"
echo "  • 每5分钟同步效果数据 (1,6,11,16...)"
echo "  • 每5分钟聚合视频数据 (2,7,12,17...)"
echo "  • 每天凌晨2点自动刷新Token"
echo ""

# 常用管理命令
echo -e "${BLUE}常用管理命令：${NC}"
echo "  查看服务状态: bash /opt/douplus/check_services.sh"
echo "  停止所有服务: bash /opt/douplus/stop_services.sh"
echo "  重启所有服务: bash /opt/douplus/restart_services.sh"
echo "  查看API日志:  tail -f $LOG_DIR/api_server.log"
echo "  查看Worker日志: tail -f $LOG_DIR/celery_worker.log"
echo ""

echo -e "${GREEN}✓ 服务启动完成！${NC}"
