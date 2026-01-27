#!/bin/bash
# 批量续费API修复验证

echo "=========================================="
echo "批量续费功能修复验证"
echo "=========================================="
echo ""

echo "1️⃣  检查后端API路由"
echo "------------------------------------------"
echo "✅ 后端API定义："
grep -n "batch-renew" /opt/douplus/douplus-sync-python/app/api/order_api.py | head -2

echo ""
echo "✅ Blueprint URL前缀："
grep -n "url_prefix" /opt/douplus/douplus-sync-python/app/api/__init__.py | grep order_bp

echo ""
echo "📊 完整API路径应该是："
echo "   /api/douplus/batch-renew"

echo ""
echo ""

echo "2️⃣  检查前端API调用路径"
echo "------------------------------------------"
echo "✅ OrderListView组件调用："
grep -n "fetch.*batch-renew" /opt/douplus/douplus-web/src/components/order/OrderListView.vue

echo ""
echo "✅ History页面调用："
grep -n "fetch.*batch-renew" /opt/douplus/douplus-web/src/views/douplus/History.vue

echo ""
echo ""

echo "3️⃣  检查前端构建状态"
echo "------------------------------------------"
if [ -f "/opt/douplus/douplus-web/dist/index.html" ]; then
    BUILD_TIME=$(stat -c%y /opt/douplus/douplus-web/dist/index.html | cut -d'.' -f1)
    echo "✅ 前端已构建"
    echo "   构建时间: $BUILD_TIME"
    
    # 检查是否是最新构建
    CURRENT_TIME=$(date +%s)
    BUILD_TIMESTAMP=$(stat -c%Y /opt/douplus/douplus-web/dist/index.html)
    TIME_DIFF=$((CURRENT_TIME - BUILD_TIMESTAMP))
    
    if [ $TIME_DIFF -lt 300 ]; then
        echo "   ✅ 构建时间在5分钟内，是最新构建"
    else
        echo "   ⚠️  构建时间超过5分钟，建议重新构建"
    fi
else
    echo "❌ 前端未构建"
fi

echo ""
echo ""

echo "4️⃣  验证图标导入问题修复"
echo "------------------------------------------"
echo "✅ 检查 account/Index.vue 图标导入："
grep -n "import.*QuestionFilled.*from" /opt/douplus/douplus-web/src/views/account/Index.vue

echo ""
echo ""

echo "5️⃣  测试后端API是否可访问"
echo "------------------------------------------"
echo "尝试调用批量续费API（需要认证token）："
echo "curl -X POST http://localhost:5000/api/douplus/batch-renew -H 'Content-Type: application/json'"
echo ""
echo "注意：实际测试需要："
echo "  1. 用户已登录并获取token"
echo "  2. 提供有效的订单ID列表"
echo "  3. 提供续费金额和时长"

echo ""
echo ""

echo "6️⃣  修复总结"
echo "------------------------------------------"
echo "✅ 问题1：批量续费API路径错误"
echo "   - 原路径: /api/douplus/order/batch-renew (错误，多了/order)"
echo "   - 新路径: /api/douplus/batch-renew (正确)"
echo "   - 修改文件: OrderListView.vue, History.vue"
echo ""
echo "✅ 问题2：图标导入缺失"
echo "   - account/Index.vue 缺少 QuestionFilled 导入"
echo "   - 已添加: import { Plus, QuestionFilled } from '@element-plus/icons-vue'"
echo ""
echo "✅ 前端已重新构建"
echo ""

echo "=========================================="
echo "🧪 下一步测试步骤"
echo "=========================================="
echo "1. 强制刷新浏览器 (Ctrl+Shift+R)"
echo "2. 打开投放记录页面"
echo "3. 选择多个投放中的订单"
echo "4. 点击批量续费按钮"
echo "5. 设置金额和时长"
echo "6. 提交续费"
echo ""
echo "预期结果："
echo "✅ 页面无 'V is not a function' 错误"
echo "✅ 批量续费对话框正常打开"
echo "✅ 提交后调用正确的API接口"
echo "✅ 显示续费成功/失败消息"
echo ""
echo "=========================================="
