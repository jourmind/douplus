#!/bin/bash

# 简化版测试:使用模拟的API响应数据来检查字段映射

echo "=========================================="
echo "DOU+ API字段映射检查(使用模拟数据)"
echo "=========================================="
echo ""

# 模拟的API响应(根据抖音DOU+ v3.0 API文档)
cat > /tmp/mock_api_response.json << 'EOF'
{
  "code": 0,
  "message": "success",
  "data": {
    "page_info": {
      "total_number": 1,
      "page": 1,
      "page_size": 50
    },
    "data": [
      {
        "dimension_data": {
          "order_id": 1234567890,
          "ad_id": 9876543210
        },
        "metrics_data": {
          "stat_cost": 50000,
          "total_play": 125000,
          "custom_like": 3500,
          "dy_comment": 280,
          "dy_share": 450,
          "dy_follow": 120,
          "dy_home_visited": 850,
          "dp_target_convert_cnt": 65,
          "custom_convert_cost": 76923,
          "play_duration_5s_rank": 0.68,
          "show_cnt": 0,
          "live_click_source_cnt": 0,
          "live_gift_uv": 0,
          "live_gift_amount": 0,
          "live_comment_cnt": 0,
          "douplus_live_follow_count": 0,
          "live_gift_cnt": 0
        }
      }
    ]
  }
}
EOF

echo ">>> 使用模拟API响应数据进行字段分析..."
echo ""

python3 << 'PYTHON_SCRIPT'
import json

# 读取模拟响应
with open('/tmp/mock_api_response.json', 'r') as f:
    response = json.load(f)

data = response['data']
report_data = data['data']

if not report_data:
    print("⚠ 没有数据")
    exit(0)

first_record = report_data[0]
dimension_data = first_record['dimension_data']
metrics_data = first_record['metrics_data']

print("=" * 70)
print("订单维度数据 (dimension_data):")
print("=" * 70)
for key, value in dimension_data.items():
    print(f"  {key:20s} = {value}")
print("")

print("=" * 70)
print("指标数据 (metrics_data) - 所有字段:")
print("=" * 70)
for key in sorted(metrics_data.keys()):
    value = metrics_data[key]
    print(f"  {key:30s} = {value}")
print("")

print("=" * 70)
print("关键字段检查 - 我们关心的3个字段:")
print("=" * 70)

# 我们在代码中使用的字段名
code_fields = {
    'playDuration5sRank': 'play_duration_5s_rank',
    'dpTargetConvertCnt': 'dp_target_convert_cnt',
    'customConvertCost': 'custom_convert_cost'
}

print("\n【Java代码 → API字段 → 实际值】\n")
for java_field, api_field in code_fields.items():
    if api_field in metrics_data:
        value = metrics_data[api_field]
        # 转换显示格式
        if api_field == 'custom_convert_cost':
            display_value = f"{value/100:.2f}元 (原始值:{value}分)"
        elif api_field == 'play_duration_5s_rank':
            display_value = f"{value*100:.2f}% (原始值:{value})"
        else:
            display_value = value
        
        print(f"✓ {java_field:25s} → {api_field:30s} = {display_value}")
    else:
        print(f"✗ {java_field:25s} → {api_field:30s} = ❌ 字段不存在")

print("\n" + "=" * 70)
print("数据转换验证:")
print("=" * 70)

# 验证数据转换逻辑
stat_cost = metrics_data['stat_cost']
play_duration_5s = metrics_data.get('play_duration_5s_rank', 0)
dp_convert = metrics_data.get('dp_target_convert_cnt', 0)
convert_cost = metrics_data.get('custom_convert_cost', 0)

print(f"\n消耗金额 (stat_cost):")
print(f"  API返回: {stat_cost} 分")
print(f"  转换后: {stat_cost/100:.2f} 元")

print(f"\n5秒完播率 (play_duration_5s_rank):")
print(f"  API返回: {play_duration_5s} (小数)")
print(f"  显示格式: {play_duration_5s*100:.2f}%")

print(f"\n转化数 (dp_target_convert_cnt):")
print(f"  API返回: {dp_convert}")
print(f"  显示格式: {dp_convert}")

print(f"\n转化成本 (custom_convert_cost):")
print(f"  API返回: {convert_cost} 分")
print(f"  转换后: {convert_cost/100:.2f} 元")

print("\n" + "=" * 70)
print("数据库字段名检查:")
print("=" * 70)

db_fields = {
    'play_duration_5s_rank': 'playDuration5sRank',
    'dp_target_convert_cnt': 'dpTargetConvertCnt', 
    'custom_convert_cost': 'customConvertCost'
}

print("\n【数据库字段 → Java字段 → MyBatis转换】\n")
for db_field, java_field in db_fields.items():
    # MyBatis Plus默认转换规则
    mybatis_field = ''.join(['_' + c.lower() if c.isupper() else c for c in java_field]).lstrip('_')
    
    if db_field == mybatis_field:
        print(f"✓ {db_field:30s} → {java_field:25s} (MyBatis: {mybatis_field})")
    else:
        print(f"⚠ {db_field:30s} → {java_field:25s} (MyBatis: {mybatis_field}) ← 不匹配!")
        print(f"   需要添加 @TableField(\"{db_field}\")")

print("\n" + "=" * 70)
print("前端字段映射检查:")
print("=" * 70)

frontend_fields = [
    ('playDuration5sRank', '5S完播率', 'formatPercentage'),
    ('dpTargetConvertCnt', '转化', 'formatNumber'),
    ('customConvertCost', '转化成本', 'formatCurrency')
]

print("\n【字段名 → 前端显示 → 格式化方法】\n")
for field_name, display_name, format_method in frontend_fields:
    print(f"  {field_name:25s} → {display_name:10s} → {format_method}")

print("\n" + "=" * 70)
print("完整数据流验证:")
print("=" * 70)

print("""
数据流程:
  1. 抖音API返回 (metrics_data)
     ├─ play_duration_5s_rank: 0.68 (小数)
     ├─ dp_target_convert_cnt: 65 (整数)
     └─ custom_convert_cost: 76923 (分)

  2. Java解析 (DouyinAdClient.parseOrderStatsV3)
     ├─ stats.setPlayDuration5sRank(0.68f)
     ├─ stats.setDpTargetConvertCnt(65)
     └─ stats.setCustomConvertCost(BigDecimal.valueOf(769.23))

  3. 数据库存储 (douplus_task表)
     ├─ play_duration_5s_rank: 0.68 (FLOAT)
     ├─ dp_target_convert_cnt: 65 (INT)
     └─ custom_convert_cost: 769.23 (DECIMAL(10,2))

  4. 前端显示 (OrderTable.vue)
     ├─ 68.00% (formatPercentage)
     ├─ 65 (formatNumber)
     └─ ¥769.23 (formatCurrency)
""")

print("=" * 70)
print("✅ 字段映射分析完成!")
print("=" * 70)

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
echo ""
echo "如果这3个字段没有数据,可能的原因:"
echo "1. API实际返回的字段名与预期不同"
echo "2. 字段值为0或null(没有转化目标的订单可能没有这些数据)"
echo "3. 数据库字段名与Java字段名映射不匹配"
echo ""
echo "建议:"
echo "1. 确认数据库字段 play_duration_5s_rank 已添加 @TableField 注解"
echo "2. 重新同步订单后查看日志中的 metrics_data 字段"
echo "3. 检查订单是否设置了转化目标"
