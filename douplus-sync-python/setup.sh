#!/bin/bash

echo "================================"
echo "DOU+ Python同步服务 - 环境准备"
echo "================================"
echo ""

# 1. 安装pip
echo ">>> 1. 安装Python pip..."
sudo apt update -qq
sudo apt install -y python3-pip python3-venv
echo "✓ pip安装完成"
echo ""

# 2. 安装Redis
echo ">>> 2. 安装Redis..."
if ! command -v redis-server &> /dev/null; then
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    echo "✓ Redis安装并启动完成"
else
    echo "✓ Redis已安装"
    sudo systemctl start redis-server 2>/dev/null || echo "Redis已在运行"
fi
echo ""

# 3. 安装Python依赖
echo ">>> 3. 安装Python依赖..."
cd /opt/douplus/douplus-sync-python
pip3 install -r requirements.txt --break-system-packages -q
echo "✓ Python依赖安装完成"
echo ""

# 4. 测试数据库连接
echo ">>> 4. 测试数据库连接..."
python3 << 'EOF'
try:
    from app.models import engine
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✓ 数据库连接成功")
except Exception as e:
    print(f"✗ 数据库连接失败: {e}")
EOF
echo ""

# 5. 测试Redis连接
echo ">>> 5. 测试Redis连接..."
if redis-cli ping | grep -q PONG; then
    echo "✓ Redis连接成功"
else
    echo "✗ Redis连接失败"
fi
echo ""

echo "================================"
echo "环境准备完成!"
echo "================================"
echo ""
echo "下一步:"
echo "  ./manage.sh start    # 启动同步服务"
echo "  ./manage.sh status   # 查看服务状态"
echo "  ./manage.sh logs     # 查看日志"
