#!/usr/bin/env python3
"""
排查投放中订单效果数据显示问题
验证数据库和API返回的数据完整性
"""

import jwt
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from app.models import SessionLocal

print("=" * 80)
print("投放中订单效果数据排查")
print("=" * 80)

# 1. 检查数据库中的投放中订单
print("\n【1】检查数据库 - 投放中订单及其效果数据")
print("-" * 80)

db = SessionLocal()
try:
    # 查询投放中订单
    query = text("""
        SELECT 
            o.id,
            o.order_id,
            o.item_id,
            o.status,
            o.order_create_time,
            COUNT(s.id) as stats_count,
            MAX(s.stat_time) as latest_stat_time
        FROM douplus_order o
        LEFT JOIN douplus_video_stats_agg s ON o.item_id = s.item_id
        WHERE o.status = 'DELIVERING'
        GROUP BY o.id, o.order_id, o.item_id, o.status, o.order_create_time
        ORDER BY o.order_create_time DESC
        LIMIT 5
    """)
    
    results = db.execute(query).fetchall()
    
    print(f"投放中订单数量: {len(results)}")
    print()
    
    for row in results:
        print(f"订单ID: {row[1]}")
        print(f"  - 视频ID: {row[2]}")
        print(f"  - 状态: {row[3]}")
        print(f"  - 创建时间: {row[4]}")
        print(f"  - 效果数据记录数: {row[5]}")
        print(f"  - 最新统计时间: {row[6]}")
        
        # 如果有效果数据，显示详细内容
        if row[5] > 0:
            stats_query = text("""
                SELECT 
                    total_cost, total_play, total_like, 
                    total_comment, total_share, total_follow,
                    total_convert, avg_convert_cost,
                    stat_time
                FROM douplus_video_stats_agg
                WHERE item_id = :item_id
                ORDER BY stat_time DESC
                LIMIT 1
            """)
            stats = db.execute(stats_query, {'item_id': row[2]}).fetchone()
            if stats:
                print(f"  - 效果数据:")
                print(f"    消耗: {stats[0]}, 播放: {stats[1]}, 点赞: {stats[2]}")
                print(f"    评论: {stats[3]}, 分享: {stats[4]}, 关注: {stats[5]}")
                print(f"    转化: {stats[6]}, 平均转化成本: {stats[7]}")
        else:
            print(f"  ⚠️  无效果数据！")
        print()
    
finally:
    db.close()

# 2. 测试API返回
print("\n【2】测试API - /api/douplus/task/page")
print("-" * 80)

# 生成有效token
token = jwt.encode({
    'user_id': 1,
    'username': 'test@test.com',
    'exp': int((datetime.utcnow() + timedelta(days=30)).timestamp())
}, 'douplus-jwt-secret-key-default', algorithm='HS256')

try:
    response = requests.get(
        'https://127.0.0.1/api/douplus/task/page',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'pageNum': 1,
            'pageSize': 5,
            'status': 'DELIVERING'
        },
        verify=False,
        timeout=10
    )
    
    data = response.json()
    
    print(f"HTTP状态码: {response.status_code}")
    print(f"业务code: {data.get('code')}")
    print(f"订单数量: {len(data.get('data', {}).get('list', []))}")
    print()
    
    if data.get('code') == 200:
        orders = data.get('data', {}).get('list', [])
        
        if orders:
            print("前3个订单的效果数据字段:")
            print()
            for i, order in enumerate(orders[:3], 1):
                print(f"订单{i} (orderId: {order.get('orderId')})")
                print(f"  itemId: {order.get('itemId')}")
                print(f"  actualCost: {order.get('actualCost')}")
                print(f"  playCount: {order.get('playCount')}")
                print(f"  likeCount: {order.get('likeCount')}")
                print(f"  shareCount: {order.get('shareCount')}")
                print(f"  commentCount: {order.get('commentCount')}")
                print(f"  followCount: {order.get('followCount')}")
                print(f"  dpTargetConvertCnt: {order.get('dpTargetConvertCnt')}")
                print()
                
                # 检查是否所有效果数据都是None/0
                has_data = any([
                    order.get('actualCost'),
                    order.get('playCount'),
                    order.get('likeCount'),
                ])
                
                if not has_data:
                    print("  ⚠️  所有效果数据字段都为空！")
                print()
        else:
            print("⚠️  API返回的订单列表为空")
    else:
        print(f"❌ API返回错误: {data.get('message')}")
        
except Exception as e:
    print(f"❌ API请求失败: {str(e)}")

# 3. 结论
print("\n【3】诊断结论")
print("=" * 80)
print("请根据以上输出判断：")
print("1. 数据库中投放中订单是否有效果数据？（stats_count > 0）")
print("2. API返回的订单是否包含效果数据字段？")
print("3. 如果数据库有但API没有 → Query层SQL关联问题")
print("4. 如果API有但前端不显示 → 前端字段映射问题")
print("=" * 80)
