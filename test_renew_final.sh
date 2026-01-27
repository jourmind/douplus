#!/bin/bash
# 续费功能最终版本验证

echo "=========================================="
echo "续费功能最终版本验证"
echo "=========================================="
echo ""

echo "1️⃣  验证单个续费对话框预算选项"
echo "------------------------------------------"
RENEW_FILE="/opt/douplus/douplus-web/src/components/order/RenewDialog.vue"

echo "✅ 预设金额选项："
grep -A 5 "const BUDGET_OPTIONS" $RENEW_FILE | head -6

echo ""
echo "✅ 默认金额值："
grep "budget: " $RENEW_FILE | grep "reactive({" -A 1 | tail -1

echo ""
echo "✅ 自定义金额配置："
grep -A 3 "v-if=\"customBudget\"" $RENEW_FILE | grep -E ":min|:max|:step"

echo ""
echo ""

echo "2️⃣  验证批量续费对话框预算选项"
echo "------------------------------------------"
BATCH_FILE="/opt/douplus/douplus-web/src/components/order/BatchRenewDialog.vue"

echo "✅ 预设金额选项："
grep -A 5 "const BUDGET_OPTIONS" $BATCH_FILE | head -6

echo ""
echo "✅ 默认金额值："
grep "budget: " $BATCH_FILE | grep "ref({" -A 1 | tail -1

echo ""
echo "✅ 自定义金额配置："
grep -A 3 "v-if=\"customBudget\"" $BATCH_FILE | grep -E ":min|:max|:step"

echo ""
echo ""

echo "3️⃣  验证前端构建"
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

echo "4️⃣  功能说明"
echo "------------------------------------------"
echo "✅ 单个订单续费："
echo "   - 预设金额：¥100、¥200、¥500、¥1000"
echo "   - 自定义金额：最低10元，步进10元，最高50000元"
echo "   - 预设时长：6小时、12小时、24小时"
echo "   - 自定义时长：最低2小时，步进2小时，最高46小时"
echo "   - 无投放笔数选项（每次仅续费一个订单）"
echo ""
echo "✅ 批量续费："
echo "   - 为多个订单续费相同的金额和时长"
echo "   - 预设金额：¥100、¥200、¥500、¥1000"
echo "   - 自定义金额：最低10元，步进10元，最高50000元"
echo "   - 预设时长：12小时、24小时、48小时"
echo "   - 自定义时长：最低2小时，步进2小时，最高46小时"
echo "   - 显示总消耗：订单数 × 单个续费金额"

echo ""
echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="
