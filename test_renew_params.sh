#!/bin/bash
# 续费功能参数验证测试

echo "=========================================="
echo "续费功能参数修改验证"
echo "=========================================="
echo ""

echo "1️⃣  检查单个续费对话框 (RenewDialog.vue)"
echo "------------------------------------------"
RENEW_FILE="/opt/douplus/douplus-web/src/components/order/RenewDialog.vue"

echo "✅ 预算选项："
grep -A 4 "const BUDGET_OPTIONS" $RENEW_FILE | head -5

echo ""
echo "✅ 自定义金额输入框配置："
grep -A 3 "v-if=\"customBudget\"" $RENEW_FILE | grep -E "min|max|step"

echo ""
echo "✅ 自定义时长输入框配置："
grep -A 3 "v-if=\"customDuration\"" $RENEW_FILE | grep -E "min|max|step|小时"

echo ""
echo ""

echo "2️⃣  检查批量续费对话框 (BatchRenewDialog.vue)"
echo "------------------------------------------"
BATCH_FILE="/opt/douplus/douplus-web/src/components/order/BatchRenewDialog.vue"

echo "✅ 预算选项："
grep -A 4 "const BUDGET_OPTIONS" $BATCH_FILE | head -5

echo ""
echo "✅ 自定义金额输入框配置："
grep -A 3 "v-if=\"customBudget\"" $BATCH_FILE | grep -E "min|max|step"

echo ""
echo "✅ 自定义时长输入框配置："
grep -A 3 "v-if=\"customDuration\"" $BATCH_FILE | grep -E "min|max|step"

echo ""
echo ""

echo "3️⃣  验证构建产物"
echo "------------------------------------------"
if [ -f "/opt/douplus/douplus-web/dist/index.html" ]; then
    echo "✅ 前端已构建: $(stat -c%y /opt/douplus/douplus-web/dist/index.html | cut -d'.' -f1)"
else
    echo "❌ 前端未构建"
fi

echo ""
echo ""

echo "4️⃣  修改内容总结"
echo "------------------------------------------"
echo "金额设置："
echo "  - 预设选项: ¥10, ¥20, ¥50, ¥100, 自定义"
echo "  - 自定义金额: 最低10元，步进10元，最高50000元"
echo ""
echo "时长设置："
echo "  - 预设选项: 6小时, 12小时, 24小时, 自定义"
echo "  - 自定义时长: 最低2小时，步进2小时，最高46小时"
echo ""
echo "适用页面："
echo "  - 单个续费对话框 (RenewDialog)"
echo "  - 批量续费对话框 (BatchRenewDialog)"

echo ""
echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="
