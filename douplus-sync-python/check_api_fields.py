#!/usr/bin/env python3
"""
检查抖音订单API返回的字段
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

db = SessionLocal()

try:
    # 获取第一个账号
    account = db.query(DouyinAccount).filter_by(deleted=0).first()
    
    print(f"账号: {account.nickname}")
    print(f"aweme_sec_uid: {account.aweme_sec_uid}\n")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
    # 创建客户端
    client = DouyinClient(access_token=access_token)
    
    try:
        # 查询订单列表
        print("正在查询订单列表...")
        order_list = client.get_order_list(
            aweme_sec_uid=account.aweme_sec_uid,
            page=1,
            page_size=10
        )
        
        if order_list:
            print(f"✅ 获取到 {len(order_list)} 个订单\n")
            
            # 显示第一个订单的完整数据结构
            first_order = order_list[0]
            print("=" * 80)
            print("第一个订单的完整数据结构:")
            print("=" * 80)
            print(json.dumps(first_order, indent=2, ensure_ascii=False))
            
            # 检查order字段
            if "order" in first_order:
                order_info = first_order["order"]
                print(f"\n{'=' * 80}")
                print("order字段包含的时间相关字段:")
                print("=" * 80)
                
                time_fields = [
                    'order_create_time',
                    'order_start_time', 
                    'order_end_time',
                    'end_time',
                    'start_time',
                    'create_time'
                ]
                
                for field in time_fields:
                    if field in order_info:
                        print(f"  ✅ {field}: {order_info[field]}")
                    else:
                        print(f"  ❌ {field}: 不存在")
                
                print(f"\n所有order字段:")
                for key in order_info.keys():
                    print(f"  - {key}")
        else:
            print("⚠️  没有订单")
            
    finally:
        client.close()
        
finally:
    db.close()
