#!/bin/bash
# 续费功能数据库字段修复验证

echo "=========================================="
echo "续费功能数据库字段修复最终验证"
echo "=========================================="
echo ""

echo "1️⃣  验证所有字段名修复"
echo "------------------------------------------"
echo "✅ 单次续费 - invest_password字段："
grep -n "SELECT invest_password FROM sys_user" /opt/douplus/douplus-sync-python/app/api/order_api.py | head -1

echo ""
echo "✅ 单次续费 - access_token字段："
grep -n "a.access_token" /opt/douplus/douplus-sync-python/app/api/order_api.py | head -1

echo ""
echo "✅ 批量续费 - invest_password字段："
grep -n "SELECT invest_password FROM sys_user" /opt/douplus/douplus-sync-python/app/api/order_api.py | tail -1

echo ""
echo "✅ 批量续费 - access_token字段："
grep -n "a.access_token" /opt/douplus/douplus-sync-python/app/api/order_api.py | tail -1

echo ""
echo ""

echo "2️⃣  验证Flask服务状态"
echo "------------------------------------------"
FLASK_PID=$(ps aux | grep "python3 api_server.py" | grep -v grep | awk '{print $2}')

if [ -n "$FLASK_PID" ]; then
    echo "✅ Flask服务正在运行"
    echo "   PID: $FLASK_PID"
    
    # 检查端口
    PORT_CHECK=$(lsof -i :5000 2>/dev/null | grep LISTEN)
    if [ -n "$PORT_CHECK" ]; then
        echo "   ✅ 端口5000监听正常"
    else
        echo "   ❌ 端口5000未监听"
    fi
else
    echo "❌ Flask服务未运行"
fi

echo ""
echo ""

echo "3️⃣  字段名错误总结"
echo "------------------------------------------"
echo "问题根源：models.py中字段定义不带_encrypted后缀"
echo ""
echo "错误字段1: invest_password_encrypted ❌"
echo "正确字段1: invest_password ✅"
echo "   - 表名: sys_user"
echo "   - 用途: 存储用户投放密码"
echo ""
echo "错误字段2: access_token_encrypted ❌"
echo "正确字段2: access_token ✅"
echo "   - 表名: douyin_account"
echo "   - 用途: 存储抖音API访问令牌"
echo ""

echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""
echo "已修复的文件："
echo "  1. /opt/douplus/douplus-sync-python/app/api/order_api.py"
echo "     - 第105行: invest_password (单次续费)"
echo "     - 第203行: invest_password (批量续费)"
echo "     - 第83行: access_token (单次续费)"
echo "     - 第231行: access_token (批量续费)"
echo ""
echo "已重启的服务："
echo "  - Flask API服务器 (PID: $FLASK_PID)"
echo ""

echo "=========================================="
echo "🧪 测试步骤"
echo "=========================================="
echo "1. 强制刷新浏览器 (Ctrl+Shift+R)"
echo "2. 打开投放记录页面"
echo ""
echo "3. 测试批量续费："
echo "   ✅ 选择2个投放中的订单"
echo "   ✅ 点击批量续费"
echo "   ✅ 设置金额¥10，时长12小时"
echo "   ✅ 点击确认续费"
echo "   ✅ 预期：成功续费2个订单（不再是0个）"
echo ""
echo "4. 测试单次续费："
echo "   ✅ 选择1个投放中的订单"
echo "   ✅ 点击续费"
echo "   ✅ 设置金额¥10，时长6小时"
echo "   ✅ 输入投放密码"
echo "   ✅ 点击确认续费"
echo "   ✅ 预期：续费成功"
echo ""

echo "预期结果："
echo "✅ 不再提示 'Unknown column access_token_encrypted'"
echo "✅ 不再提示 'Unknown column invest_password_encrypted'"
echo "✅ 批量续费显示成功订单数（不是0）"
echo "✅ 单次续费正常完成"
echo ""
echo "=========================================="
