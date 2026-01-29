#!/usr/bin/env python3
"""
直接调用抖音API，查看返回的原始订单ID

对比抖音API返回的order_id与DOU+后台显示的order_id
"""

import sys
import os

# 添加项目路径
project_path = '/opt/douplus/douplus-sync-python'
sys.path.insert(0, project_path)
os.chdir(project_path)

from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

# DOU+后台真实订单ID（前5个）
REAL_ORDER_IDS = [
    '1855548567381076',
    '1855548553415739',
    '1855548517984355',
    '1855548548789328',
    '1855548523186375',
]

def debug_api_order_ids():
    """调试抖音API返回的订单ID"""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("抖音API订单ID调试")
        print("=" * 80)
        
        # 1. 获取账号5的信息
        account = db.query(DouyinAccount).filter(DouyinAccount.id == 5).first()
        if not account:
            print("❌ 账号5不存在")
            return
        
        print(f"\n账号信息:")
        print(f"  ID: {account.id}")
        print(f"  昵称: {account.nickname}")
        print(f"  aweme_sec_uid: {account.aweme_sec_uid}")
        
        # 2. 解密token并创建客户端
        access_token = decrypt_access_token(account.access_token)
        client = DouyinClient(access_token)
        
        try:
            # 3. 调用API获取订单列表（第1页）
            print(f"\n调用API获取订单列表...")
            orders = client.get_order_list(
                aweme_sec_uid=account.aweme_sec_uid,
                page=1,
                page_size=20
            )
            
            print(f"\nAPI返回订单数: {len(orders)}")
            
            # 4. 显示前10个订单的ID
            print(f"\n前10个订单的完整数据结构:")
            print(f"{'序号':<5} {'API返回order_id':<20} {'创建时间':<20}")
            print("-" * 60)
            
            for i, order_data in enumerate(orders[:10], 1):
                order_info = order_data.get("order", {})
                order_id = order_info.get("order_id")
                create_time = order_info.get("order_create_time", "")
                print(f"{i:<5} {str(order_id):<20} {create_time:<20}")
                
                # 打印第一个订单的完整结构
                if i == 1:
                    print(f"\n第1个订单的完整JSON结构:")
                    print(json.dumps(order_data, indent=2, ensure_ascii=False)[:1000] + "...\n")
            
            # 5. 对比DOU+后台的真实订单ID
            print(f"\n对比DOU+后台真实订单ID:")
            print(f"{'DOU+后台真实ID':<20} {'API返回ID':<20} {'匹配状态'}")
            print("-" * 60)
            
            api_order_ids = []
            for order_data in orders[:10]:
                order_info = order_data.get("order", {})
                api_order_ids.append(str(order_info.get("order_id")))
            
            for real_id in REAL_ORDER_IDS:
                if real_id in api_order_ids:
                    api_index = api_order_ids.index(real_id)
                    print(f"{real_id:<20} {api_order_ids[api_index]:<20} ✓ 匹配")
                else:
                    # 查找相似的（前12位相同）
                    similar = [aid for aid in api_order_ids if aid[:12] == real_id[:12]]
                    if similar:
                        print(f"{real_id:<20} {similar[0]:<20} ⚠️  末尾不同")
                    else:
                        print(f"{real_id:<20} {'未找到':<20} ❌ 不匹配")
            
            print("\n" + "=" * 80)
            
        finally:
            client.close()
        
    except Exception as e:
        print(f"✗ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    debug_api_order_ids()
