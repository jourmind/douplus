#!/bin/bash
# 测试视频ID筛选与投放状态组合筛选功能

BASE_URL="https://douplus.easymai.cn/api"

echo "========================================================================"
echo "测试视频ID筛选与投放状态组合筛选功能"
echo "========================================================================"
echo ""

# 需要替换为真实的认证token
read -p "请输入认证Token (从浏览器开发者工具中获取): " AUTH_TOKEN

if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ 未提供Token，无法测试"
    exit 1
fi

echo ""
echo "========================================================================"
echo "测试1：查询所有订单（不带筛选条件）"
echo "========================================================================"
curl -s -X GET "${BASE_URL}/query/task/page?pageNum=1&pageSize=5" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  | jq '{code: .code, message: .message, total: .data.total, count: (.data.list | length)}'

echo ""
echo "========================================================================"
echo "测试2：按视频ID精确搜索"
echo "========================================================================"
read -p "请输入要搜索的视频ID (例如: 7453835850963258665): " VIDEO_ID

if [ -n "$VIDEO_ID" ]; then
    echo "搜索视频ID: $VIDEO_ID"
    curl -s -X GET "${BASE_URL}/query/task/page?pageNum=1&pageSize=10&keyword=${VIDEO_ID}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      | jq '{
          code: .code, 
          total: .data.total, 
          orders: .data.list | map({
              order_id: .orderId, 
              item_id: .itemId, 
              title: .awemeTitle, 
              status: .status
          })
      }'
else
    echo "⚠️  跳过测试2"
fi

echo ""
echo "========================================================================"
echo "测试3：视频ID + 投放状态组合筛选"
echo "========================================================================"
if [ -n "$VIDEO_ID" ]; then
    echo "搜索条件: 视频ID=$VIDEO_ID, 状态=DELIVERING"
    curl -s -X GET "${BASE_URL}/query/task/page?pageNum=1&pageSize=10&keyword=${VIDEO_ID}&status=DELIVERING" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      | jq '{
          code: .code, 
          total: .data.total, 
          orders: .data.list | map({
              order_id: .orderId, 
              item_id: .itemId, 
              title: .awemeTitle, 
              status: .status
          })
      }'
else
    echo "⚠️  跳过测试3"
fi

echo ""
echo "========================================================================"
echo "测试4：视频标题模糊搜索（向后兼容）"
echo "========================================================================"
read -p "请输入视频标题关键词 (例如: 如何): " TITLE_KEYWORD

if [ -n "$TITLE_KEYWORD" ]; then
    echo "搜索关键词: $TITLE_KEYWORD"
    curl -s -X GET "${BASE_URL}/query/task/page?pageNum=1&pageSize=10&keyword=${TITLE_KEYWORD}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      | jq '{
          code: .code, 
          total: .data.total, 
          count: (.data.list | length),
          titles: .data.list | map(.awemeTitle) | unique
      }'
else
    echo "⚠️  跳过测试4"
fi

echo ""
echo "========================================================================"
echo "测试5：视频ID + 账号ID + 投放状态 多重组合筛选"
echo "========================================================================"
read -p "请输入账号ID (例如: 6): " ACCOUNT_ID

if [ -n "$VIDEO_ID" ] && [ -n "$ACCOUNT_ID" ]; then
    echo "搜索条件: 视频ID=$VIDEO_ID, 账号ID=$ACCOUNT_ID, 状态=DELIVERING"
    curl -s -X GET "${BASE_URL}/query/task/page?pageNum=1&pageSize=10&keyword=${VIDEO_ID}&accountId=${ACCOUNT_ID}&status=DELIVERING" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      | jq '{
          code: .code, 
          total: .data.total, 
          orders: .data.list | map({
              order_id: .orderId, 
              item_id: .itemId, 
              account_id: .accountId,
              status: .status
          })
      }'
else
    echo "⚠️  跳过测试5（需要视频ID和账号ID）"
fi

echo ""
echo "========================================================================"
echo "测试6：数据导出API（验证筛选条件是否同步）"
echo "========================================================================"
if [ -n "$VIDEO_ID" ]; then
    echo "导出条件: 视频ID=$VIDEO_ID, 状态=DELIVERING"
    echo "注意：此接口返回Excel文件，这里仅检查HTTP状态码"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "${BASE_URL}/export/orders" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"keyword\": \"${VIDEO_ID}\", \"status\": \"DELIVERING\"}")
    
    echo "HTTP状态码: $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ 导出API正常工作"
    else
        echo "❌ 导出API返回错误码: $HTTP_CODE"
    fi
else
    echo "⚠️  跳过测试6"
fi

echo ""
echo "========================================================================"
echo "✅ 测试完成"
echo "========================================================================"
echo ""
echo "验证要点："
echo "1. ✓ 视频ID精确匹配应只返回该视频的订单"
echo "2. ✓ 视频ID + 投放状态组合筛选应正确过滤"
echo "3. ✓ 向后兼容视频标题模糊搜索"
echo "4. ✓ 支持多重筛选条件组合（视频ID + 账号 + 状态 + 日期）"
echo "5. ✓ 导出功能应使用相同的筛选逻辑"
echo ""
