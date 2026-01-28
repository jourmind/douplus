#!/usr/bin/env python3
"""
检查抖音订单列表API返回的数据结构
"""

from datetime import datetime, timedelta
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

print("=" * 80)
print("检查抖音订单列表API")
print("=" * 80)

# 获取账号5
db = SessionLocal()
try:
    account = db.query(DouyinAccount).filter(DouyinAccount.id == 5).first()
    if not account:
        print("账号5不存在")
        exit(1)
    
    print(f"\n账号: {account.nickname}")
    print(f"AdvertiserId: {account.advertiser_id}")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
finally:
    db.close()

# 调用订单列表API
client = DouyinClient(access_token)

try:
    print("\n调用订单列表API...")
    print("-" * 80)
    
    # 调用订单列表API
    orders = client.get_order_list(
        aweme_sec_uid=account.aweme_sec_uid,
        page=1,
        page_size=10
    )
    
    print(f"\n返回订单数量: {len(orders) if orders else 0}")
    
    if orders:
        # 查看第一个订单的完整字段
        first_order = orders[0]
        
        print("\n第一个订单的所有字段:")
        print("-" * 80)
        for key in sorted(first_order.keys()):
            value = first_order[key]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {key:30s}: {value}")
        
        print("\n" + "=" * 80)
        print("检查效果数据字段")
        print("=" * 80)
        
        effect_fields = [
            'play_count', 'playCount', 'total_play',
            'like_count', 'likeCount', 'custom_like',
            'share_count', 'shareCount', 'dy_share',
            'comment_count', 'commentCount', 'dy_comment',
            'convert_count', 'convertCount', 'dp_target_convert_cnt',
            'actual_cost', 'actualCost', 'stat_cost'
        ]
        
        found_fields = []
        for field in effect_fields:
            if field in first_order:
                found_fields.append(f"{field} = {first_order[field]}")
        
        if found_fields:
            print("\n✅ 找到效果数据字段:")
            for f in found_fields:
                print(f"  {f}")
        else:
            print("\n❌ 未找到任何效果数据字段")
            print("   订单列表API不包含效果数据")
        
        # 显示前3个订单的基本信息
        print("\n" + "=" * 80)
        print("前3个订单概览")
        print("=" * 80)
        for i, order in enumerate(orders[:3], 1):
            print(f"\n订单{i}:")
            print(f"  order_id: {order.get('order_id')}")
            print(f"  item_id: {order.get('item_id')}")
            print(f"  status: {order.get('status')}")
            print(f"  budget: {order.get('budget')}")
            
    else:
        print("⚠️  API未返回任何订单")
        
finally:
    client.close()

print("\n" + "=" * 80)
