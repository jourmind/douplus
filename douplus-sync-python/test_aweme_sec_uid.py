#!/usr/bin/env python3
"""
测试使用正确的aweme_sec_uid调用效果报告API
按照官方文档要求，不传order_ids，获取所有订单的效果数据
"""

from datetime import datetime, timedelta
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

print("=" * 80)
print("测试效果报告API（不传order_ids）")
print("=" * 80)

# 获取账号5
db = SessionLocal()
try:
    account = db.query(DouyinAccount).filter(DouyinAccount.id == 5).first()
    if not account:
        print("账号5不存在")
        exit(1)
    
    print(f"\n账号: {account.nickname}")
    print(f"advertiser_id: {account.advertiser_id}")
    print(f"aweme_sec_uid: {account.aweme_sec_uid}")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
finally:
    db.close()

# 调用API
client = DouyinClient(access_token)

try:
    # 测试1：查询最近1天的数据（包含今天）
    print("\n" + "=" * 80)
    print("测试1：查询最近1天数据")
    print("=" * 80)
    
    begin_time = datetime.now().strftime("%Y-%m-%d")
    end_time = datetime.now().strftime("%Y-%m-%d")
    
    print(f"时间范围: {begin_time} ~ {end_time}")
    print(f"aweme_sec_uid: {account.aweme_sec_uid}")
    
    stats_dict = client.get_order_report(
        aweme_sec_uid=account.aweme_sec_uid,
        begin_time=begin_time,
        end_time=end_time
    )
    
    print(f"\n返回订单数: {len(stats_dict) if stats_dict else 0}")
    
    if stats_dict:
        # 检查投放中订单的数据
        target_order_ids = [
            '1855431292118059',
            '1855431281987752',
            '1855431261360420'
        ]
        
        print("\n检查投放中订单的效果数据:")
        for oid in target_order_ids:
            if oid in stats_dict:
                stats = stats_dict[oid]
                print(f"\n✅ 订单 {oid}:")
                print(f"   item_id: {stats.get('item_id')}")
                print(f"   播放: {stats.get('total_play')}")
                print(f"   点赞: {stats.get('custom_like')}")
                print(f"   消耗: {stats.get('stat_cost')}")
            else:
                print(f"\n❌ 订单 {oid}: API未返回数据")
        
        # 显示前5个订单
        print("\n" + "-" * 80)
        print("API返回的前5个订单:")
        for i, (order_id, stats) in enumerate(list(stats_dict.items())[:5], 1):
            print(f"\n订单{i}: {order_id}")
            print(f"  播放: {stats.get('total_play')}")
            print(f"  点赞: {stats.get('custom_like')}")
            print(f"  消耗: {stats.get('stat_cost')}")
    else:
        print("\n⚠️  API未返回任何数据")
    
    # 测试2：查询最近2天
    print("\n" + "=" * 80)
    print("测试2：查询最近2天数据")
    print("=" * 80)
    
    begin_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_time = datetime.now().strftime("%Y-%m-%d")
    
    print(f"时间范围: {begin_time} ~ {end_time}")
    
    stats_dict2 = client.get_order_report(
        aweme_sec_uid=account.aweme_sec_uid,
        begin_time=begin_time,
        end_time=end_time
    )
    
    print(f"\n返回订单数: {len(stats_dict2) if stats_dict2 else 0}")
    
    if stats_dict2:
        # 再次检查投放中订单
        found_count = 0
        for oid in target_order_ids:
            if oid in stats_dict2:
                found_count += 1
        
        print(f"\n投放中订单匹配数: {found_count}/{len(target_order_ids)}")
        
finally:
    client.close()

print("\n" + "=" * 80)
