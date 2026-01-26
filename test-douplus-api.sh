#!/bin/bash

# 测试DOU+订单数据报告API,查看实际返回的字段

echo "=========================================="
echo "DOU+ 订单报告API实际返回数据测试"
echo "=========================================="
echo ""

# 数据库密码
DB_PASSWORD="XgX2B5Kn7SAKMTnG"

# 从数据库获取账号信息
echo ">>> 1. 获取账号信息..."
ACCOUNT_DATA=$(mysql -u root -p"${DB_PASSWORD}" douplus -N -e "
SELECT id, access_token, aweme_sec_uid, nickname 
FROM douyin_account 
WHERE status = 1 
LIMIT 1;
" 2>/dev/null)

if [ -z "$ACCOUNT_DATA" ]; then
    echo "❌ 未找到有效账号"
    exit 1
fi

ACCOUNT_ID=$(echo "$ACCOUNT_DATA" | awk '{print $1}')
ACCESS_TOKEN_BASE64=$(echo "$ACCOUNT_DATA" | awk '{print $2}')
AWEME_SEC_UID=$(echo "$ACCOUNT_DATA" | awk '{print $3}')
NICKNAME=$(echo "$ACCOUNT_DATA" | awk '{print $4}')

# 解密AccessToken
ACCESS_TOKEN=$(echo "$ACCESS_TOKEN_BASE64" | base64 -d)

echo "✓ 账号ID: $ACCOUNT_ID"
echo "✓ 账号昵称: $NICKNAME"
echo "✓ aweme_sec_uid: $AWEME_SEC_UID"
echo ""

# 获取一个订单用于测试
echo ">>> 2. 获取订单数据..."
ORDER_DATA=$(mysql -u root -p"${DB_PASSWORD}" douplus -N -e "
SELECT order_id, actual_cost, play_count 
FROM douplus_task 
WHERE account_id = $ACCOUNT_ID 
AND order_id IS NOT NULL 
AND order_id != '' 
LIMIT 1;
" 2>/dev/null)

if [ -z "$ORDER_DATA" ]; then
    echo "⚠ 没有找到订单,将查询全部"
    ORDER_IDS_JSON=""
else
    ORDER_ID=$(echo "$ORDER_DATA" | awk '{print $1}')
    echo "✓ 测试订单ID: $ORDER_ID"
    ORDER_IDS_JSON="\"$ORDER_ID\""
fi
echo ""

# 时间范围
BEGIN_TIME=$(date -d "30 days ago" +%Y-%m-%d)
END_TIME=$(date +%Y-%m-%d)

echo ">>> 3. 调用订单数据报告API..."
echo "时间范围: $BEGIN_TIME ~ $END_TIME"
echo ""

# 构建请求
if [ -n "$ORDER_IDS_JSON" ]; then
    REQUEST_JSON="{\"aweme_sec_uid\":\"$AWEME_SEC_UID\",\"order_ids\":[$ORDER_IDS_JSON],\"begin_time\":\"$BEGIN_TIME\",\"end_time\":\"$END_TIME\"}"
else
    REQUEST_JSON="{\"aweme_sec_uid\":\"$AWEME_SEC_UID\",\"begin_time\":\"$BEGIN_TIME\",\"end_time\":\"$END_TIME\"}"
fi

# 调用API
API_URL="https://api.oceanengine.com/open_api/v3.0/douplus/order/report/"

echo "请求JSON: $REQUEST_JSON"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Access-Token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON")

# 检查响应
CODE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code', -1))" 2>/dev/null)

if [ "$CODE" != "0" ]; then
    echo "❌ API调用失败!"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

echo "✅ API调用成功!"
echo ""

# 分析返回数据
python3 << EOF
import json
import sys

response_text = '''$RESPONSE'''
try:
    response = json.loads(response_text)
except Exception as e:
    print(f"❌ JSON解析失败: {e}")
    sys.exit(1)

data = response.get('data', {})
page_info = data.get('page_info', {})
report_data = data.get('data', [])

total = page_info.get('total_number', 0)
count = len(report_data)

print("=" * 70)
print(f"订单数据总览")
print("=" * 70)
print(f"总记录数: {total}")
print(f"当前返回: {count} 条")
print("")

if count == 0:
    print("⚠ 没有返回订单数据")
    sys.exit(0)

# 分析第一条记录
record = report_data[0]
dimension = record.get('dimension_data', {})
metrics = record.get('metrics_data', {})

print("=" * 70)
print("第一条订单数据分析")
print("=" * 70)
print(f"订单ID: {dimension.get('order_id', 'N/A')}")
print("")

print("【metrics_data 所有字段及值】")
print("-" * 70)
for key in sorted(metrics.keys()):
    value = metrics[key]
    print(f"  {key:35s} = {value}")
print("")

# 重点检查3个缺失的字段
print("=" * 70)
print("重点检查缺失的3个字段")
print("=" * 70)

target_fields = {
    'play_duration_5s_rank': ('5秒完播率', 'float'),
    'dp_target_convert_cnt': ('转化数', 'int'),
    'custom_convert_cost': ('转化成本(分)', 'int')
}

for field, (desc, dtype) in target_fields.items():
    exists = field in metrics
    value = metrics.get(field, 'N/A')
    
    status = "✓" if exists else "✗"
    print(f"{status} {desc:15s} ({field:30s})")
    print(f"   值: {value}")
    print(f"   类型: {type(value).__name__}")
    
    # 如果是转化成本,转换为元
    if field == 'custom_convert_cost' and exists and value != 'N/A':
        yuan = value / 100.0
        print(f"   转换: {yuan:.2f} 元")
    
    # 如果是5秒完播率,转换为百分比
    if field == 'play_duration_5s_rank' and exists and value != 'N/A':
        percent = value * 100
        print(f"   转换: {percent:.2f}%")
    
    print("")

# 检查数据库存储
print("=" * 70)
print("检查数据库中的订单数据")
print("=" * 70)

EOF

# 查询数据库中对应订单的数据
if [ -n "$ORDER_ID" ]; then
    echo ">>> 查询订单 $ORDER_ID 在数据库中的存储情况..."
    mysql -u root -p"${DB_PASSWORD}" douplus -e "
    SELECT 
        order_id,
        actual_cost AS '消耗(元)',
        play_count AS '播放量',
        play_duration_5s_rank AS '5秒完播率',
        dp_target_convert_cnt AS '转化数',
        custom_convert_cost AS '转化成本(元)'
    FROM douplus_task 
    WHERE order_id = '$ORDER_ID';
    " 2>/dev/null
fi

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
echo ""
echo "如果3个字段都存在但数据库中为空,可能原因:"
echo "1. Service层更新逻辑有问题"
echo "2. 字段名映射不正确"
echo "3. 数据类型转换问题"
echo ""
echo "请查看上面的输出,对比API返回和数据库存储的差异"
