#!/usr/bin/env python3
"""
直接调用抖音效果报告API查看原始返回数据
"""

from datetime import datetime, timedelta
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

print("=" * 80)
print("直接调用抖音效果报告API")
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
    print(f"AwemeSecUid: {account.aweme_sec_uid}")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
finally:
    db.close()

# 调用API
client = DouyinClient(access_token)

try:
    # 查询最近7天的效果数据
    begin_time = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_time = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n查询时间范围: {begin_time} ~ {end_time}")
    print("-" * 80)
    
    stats_dict = client.get_order_report(
        aweme_sec_uid=account.aweme_sec_uid,
        begin_time=begin_time,
        end_time=end_time
    )
    
    print(f"\n返回数据条数: {len(stats_dict) if stats_dict else 0}")
    print()
    
    if stats_dict:
        print("返回的视频ID列表:")
        for item_id, stats in list(stats_dict.items())[:10]:
            print(f"  视频ID: {item_id}")
            print(f"    播放: {stats.get('total_play', 0)}")
            print(f"    点赞: {stats.get('total_like', 0)}")
            print(f"    消耗: {stats.get('total_cost', 0)}")
            print()
        
        # 检查是否包含投放中订单的视频ID
        target_item_id = '7599151828067962122'
        if target_item_id in stats_dict:
            print(f"✅ 包含投放中订单的视频ID: {target_item_id}")
            print(f"   数据: {stats_dict[target_item_id]}")
        else:
            print(f"❌ 不包含投放中订单的视频ID: {target_item_id}")
            print(f"   返回的视频ID: {list(stats_dict.keys())[:5]}")
    else:
        print("⚠️  API未返回任何数据")
        
finally:
    client.close()

print("\n" + "=" * 80)
