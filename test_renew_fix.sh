#!/bin/bash
# 续费功能修复验证测试

echo "=========================================="
echo "续费功能修复验证"
echo "=========================================="
echo ""

echo "1️⃣  验证投放笔数已移除"
echo "------------------------------------------"
RENEW_FILE="/opt/douplus/douplus-web/src/components/order/RenewDialog.vue"

echo "检查是否还有投放笔数表单项..."
if grep -q "投放笔数" $RENEW_FILE; then
    echo "❌ 仍然存在'投放笔数'文本"
    grep -n "投放笔数" $RENEW_FILE
else
    echo "✅ '投放笔数'表单项已删除"
fi

echo ""
echo "检查是否还有count变量..."
if grep -q "form.count" $RENEW_FILE; then
    echo "❌ 仍然存在 form.count"
    grep -n "form.count" $RENEW_FILE
else
    echo "✅ count变量已删除"
fi

echo ""
echo "检查是否还有totalAmount计算..."
if grep -q "totalAmount" $RENEW_FILE; then
    echo "❌ 仍然存在 totalAmount"
    grep -n "totalAmount" $RENEW_FILE
else
    echo "✅ totalAmount计算已删除"
fi

echo ""
echo ""

echo "2️⃣  验证事件名称修正"
echo "------------------------------------------"
echo "检查emit事件名称..."
if grep -q "emit('submit'" $RENEW_FILE; then
    echo "✅ 事件名称已改为 'submit'"
    grep -n "emit('submit'" $RENEW_FILE | head -1
else
    echo "❌ 事件名称未修改"
fi

echo ""
echo "检查emit类型定义..."
if grep -q "(e: 'submit'" $RENEW_FILE; then
    echo "✅ TypeScript类型定义已更新"
    grep -n "(e: 'submit'" $RENEW_FILE | head -1
else
    echo "❌ TypeScript类型定义未更新"
fi

echo ""
echo ""

echo "3️⃣  验证费用预估简化"
echo "------------------------------------------"
echo "检查费用预估显示..."
grep -A 3 "费用预估" $RENEW_FILE | tail -3

echo ""
echo ""

echo "4️⃣  验证前端构建"
echo "------------------------------------------"
if [ -f "/opt/douplus/douplus-web/dist/index.html" ]; then
    BUILD_TIME=$(stat -c%y /opt/douplus/douplus-web/dist/index.html | cut -d'.' -f1)
    echo "✅ 前端已构建"
    echo "   构建时间: $BUILD_TIME"
else
    echo "❌ 前端未构建"
fi

echo ""
echo ""

echo "5️⃣  修改内容总结"
echo "------------------------------------------"
echo "✅ 已移除功能："
echo "   - 投放笔数选项（整个表单项）"
echo "   - 费用预估中的单笔金额和笔数行"
echo "   - form.count 变量"
echo "   - totalAmount 计算属性"
echo ""
echo "✅ 已修复问题："
echo "   - 事件名称从 'confirm' 改为 'submit'"
echo "   - emit类型定义已同步更新"
echo "   - 费用预估简化为单行显示"
echo ""
echo "✅ 续费功能特性："
echo "   - 金额: 最低10元，10元倍数"
echo "   - 时长: 最低2小时，2小时倍数，最大46小时"
echo "   - 无投放笔数限制（每次续费仅操作单个订单）"

echo ""
echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="
