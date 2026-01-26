#!/bin/bash

# 测试脚本:获取DOU+订单数据报告API响应,检查字段映射关系

echo "=========================================="
echo "DOU+ 订单数据报告API字段测试"
echo "=========================================="
echo ""

# 从.env文件读取配置
source /opt/douplus/.env

# 数据库查询获取第一个有效账号
echo ">>> 1. 从数据库获取测试账号信息..."
ACCOUNT_INFO=$(mysql -u root -p"${MYSQL_PASSWORD}" -D douplus -N -e "
SELECT id, access_token, aweme_sec_uid 
FROM douyin_account 
WHERE status = 1 
AND aweme_sec_uid IS NOT NULL 
AND aweme_sec_uid != '' 
LIMIT 1;
" 2>/dev/null)

if [ -z "$ACCOUNT_INFO" ]; then
    echo "❌ 未找到有效的抖音账号"
    exit 1
fi

ACCOUNT_ID=$(echo "$ACCOUNT_INFO" | awk '{print $1}')
ACCESS_TOKEN_BASE64=$(echo "$ACCOUNT_INFO" | awk '{print $2}')
AWEME_SEC_UID=$(echo "$ACCOUNT_INFO" | awk '{print $3}')

# 解码AccessToken
ACCESS_TOKEN=$(echo "$ACCESS_TOKEN_BASE64" | base64 -d)

echo "✓ 账号ID: $ACCOUNT_ID"
echo "✓ aweme_sec_uid: $AWEME_SEC_UID"
echo "✓ Access Token: ${ACCESS_TOKEN:0:20}..."
echo ""

# 获取一个订单ID用于测试
echo ">>> 2. 从数据库获取一个订单ID..."
ORDER_ID=$(mysql -u root -p"${MYSQL_PASSWORD}" -D douplus -N -e "
SELECT order_id 
FROM douplus_task 
WHERE account_id = $ACCOUNT_ID 
AND order_id IS NOT NULL 
AND order_id != '' 
LIMIT 1;
" 2>/dev/null)

if [ -z "$ORDER_ID" ]; then
    echo "⚠ 未找到已有订单,将查询全部订单"
    ORDER_IDS=""
else
    echo "✓ 测试订单ID: $ORDER_ID"
    ORDER_IDS="\"$ORDER_ID\""
fi
echo ""

# 设置时间范围(最近30天)
BEGIN_TIME=$(date -d "30 days ago" +%Y-%m-%d)
END_TIME=$(date +%Y-%m-%d)

echo ">>> 3. 调用DOU+订单数据报告API..."
echo "时间范围: $BEGIN_TIME ~ $END_TIME"
echo ""

# 构建请求JSON
if [ -n "$ORDER_IDS" ]; then
    REQUEST_JSON="{\"aweme_sec_uid\":\"$AWEME_SEC_UID\",\"order_ids\":[$ORDER_IDS],\"begin_time\":\"$BEGIN_TIME\",\"end_time\":\"$END_TIME\"}"
else
    REQUEST_JSON="{\"aweme_sec_uid\":\"$AWEME_SEC_UID\",\"begin_time\":\"$BEGIN_TIME\",\"end_time\":\"$END_TIME\"}"
fi

# 调用API
API_URL="https://api.oceanengine.com/open_api/v3.0/douplus/order/report/"

echo "请求URL: $API_URL"
echo "请求参数: $REQUEST_JSON"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Access-Token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON")

echo "=========================================="
echo "API响应 (完整JSON)"
echo "=========================================="
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# 检查响应状态
CODE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code', -1))" 2>/dev/null)

if [ "$CODE" != "0" ]; then
    MESSAGE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message', 'Unknown error'))" 2>/dev/null)
    echo "❌ API调用失败: code=$CODE, message=$MESSAGE"
    exit 1
fi

echo "✅ API调用成功!"
echo ""

# 提取并分析metrics_data字段
echo "=========================================="
echo "metrics_data 字段分析"
echo "=========================================="

python3 << 'PYTHON_SCRIPT'
import sys
import json

# 读取响应
response_text = """RESPONSE_PLACEHOLDER"""
try:
    response = json.loads(response_text)
except:
    print("❌ 无法解析JSON响应")
    sys.exit(1)

# 提取数据
data = response.get('data', {})
page_info = data.get('page_info', {})
report_data = data.get('data', [])

print(f"总记录数: {page_info.get('total_number', 0)}")
print(f"当前页记录数: {len(report_data)}")
print("")

if not report_data:
    print("⚠ 没有返回订单数据")
    sys.exit(0)

# 分析第一条记录
first_record = report_data[0]
dimension_data = first_record.get('dimension_data', {})
metrics_data = first_record.get('metrics_data', {})

print("=" * 50)
print("第一条订单数据:")
print("=" * 50)
print(f"订单ID: {dimension_data.get('order_id', 'N/A')}")
print("")

print("【metrics_data 包含的所有字段】")
print("-" * 50)
for key in sorted(metrics_data.keys()):
    value = metrics_data[key]
    print(f"  {key:30s} = {value}")
print("")

# 检查关键字段
print("=" * 50)
print("关键字段检查:")
print("=" * 50)

# 检查我们关心的3个字段
fields_to_check = {
    'play_duration_5s_rank': '5秒完播率',
    'dp_target_convert_cnt': '转化数',
    'custom_convert_cost': '转化成本'
}

for field_name, field_desc in fields_to_check.items():
    if field_name in metrics_data:
        value = metrics_data[field_name]
        print(f"✓ {field_desc:15s} ({field_name:25s}) = {value}")
    else:
        print(f"✗ {field_desc:15s} ({field_name:25s}) = 字段不存在")

print("")

# 显示其他可能相关的字段
print("=" * 50)
print("其他可能相关的字段:")
print("=" * 50)

# 查找包含这些关键词的字段
keywords = ['convert', 'duration', 'play', 'rank', 'cost', 'completion']
found_related = False

for key in sorted(metrics_data.keys()):
    for keyword in keywords:
        if keyword.lower() in key.lower():
            value = metrics_data[key]
            print(f"  {key:30s} = {value}")
            found_related = True
            break

if not found_related:
    print("  未找到相关字段")

print("")
print("=" * 50)
print("完整的 metrics_data (JSON格式):")
print("=" * 50)
print(json.dumps(metrics_data, indent=2, ensure_ascii=False))

PYTHON_SCRIPT

# 替换Python脚本中的占位符
python3 << PYTHON_SCRIPT
import sys
import json

response_text = '''$RESPONSE'''
try:
    response = json.loads(response_text)
except Exception as e:
    print(f"❌ 无法解析JSON响应: {e}")
    sys.exit(1)

# 提取数据
data = response.get('data', {})
page_info = data.get('page_info', {})
report_data = data.get('data', [])

print(f"总记录数: {page_info.get('total_number', 0)}")
print(f"当前页记录数: {len(report_data)}")
print("")

if not report_data:
    print("⚠ 没有返回订单数据")
    sys.exit(0)

# 分析第一条记录
first_record = report_data[0]
dimension_data = first_record.get('dimension_data', {})
metrics_data = first_record.get('metrics_data', {})

print("=" * 50)
print("第一条订单数据:")
print("=" * 50)
print(f"订单ID: {dimension_data.get('order_id', 'N/A')}")
print("")

print("【metrics_data 包含的所有字段】")
print("-" * 50)
for key in sorted(metrics_data.keys()):
    value = metrics_data[key]
    print(f"  {key:30s} = {value}")
print("")

# 检查关键字段
print("=" * 50)
print("关键字段检查:")
print("=" * 50)

# 检查我们关心的3个字段
fields_to_check = {
    'play_duration_5s_rank': '5秒完播率',
    'dp_target_convert_cnt': '转化数',
    'custom_convert_cost': '转化成本'
}

for field_name, field_desc in fields_to_check.items():
    if field_name in metrics_data:
        value = metrics_data[field_name]
        print(f"✓ {field_desc:15s} ({field_name:25s}) = {value}")
    else:
        print(f"✗ {field_desc:15s} ({field_name:25s}) = 字段不存在")

print("")

# 显示其他可能相关的字段
print("=" * 50)
print("其他可能相关的字段:")
print("=" * 50)

# 查找包含这些关键词的字段
keywords = ['convert', 'duration', 'play', 'rank', 'cost', 'completion', 'rate', 'finish']
found_related = []

for key in sorted(metrics_data.keys()):
    for keyword in keywords:
        if keyword.lower() in key.lower():
            value = metrics_data[key]
            found_related.append(f"  {key:30s} = {value}")
            break

if found_related:
    for item in sorted(set(found_related)):
        print(item)
else:
    print("  未找到相关字段")

print("")
print("=" * 50)
print("完整的 metrics_data (JSON格式):")
print("=" * 50)
print(json.dumps(metrics_data, indent=2, ensure_ascii=False))

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
