#!/usr/bin/env python3
"""
测试抖音API返回的订单数据结构
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
import json

db = SessionLocal()

try:
    # 获取账号ID=5的账号
    account = db.query(DouyinAccount).filter_by(id=5, deleted=0).first()
    
    if not account:
        print("❌ 没有找到账号")
        exit(1)
    
    print(f"✅ 使用账号: {account.nickname} (ID: {account.id})")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
    # 创建客户端
    client = DouyinClient(access_token=access_token)
    
    try:
        # 查询订单列表
        print(f"\n正在查询订单列表...")
        result = client.get_order_list(
            aweme_sec_uid=account.aweme_sec_uid,
            page=1,
            page_size=10
        )
        
        if result and len(result) > 0:
            # 找第一个DELIVERING状态的订单
            order_data = None
            for item in result:
                if item.get("order", {}).get("task_status") == "DELIVERING":
                    order_data = item
                    break
            
            if not order_data:
                order_data = result[0]
                print(f"\n⚠️  没有找到DELIVERING状态的订单，显示第一个订单")
            
            print(f"\n✅ 订单数据结构:\n")
            print(json.dumps(order_data, indent=2, ensure_ascii=False))
            
            # 提取关键字段
            order_info = order_data.get("order", {})
            print(f"\n\n🔍 订单关键字段:")
            print(f"  order_id: {order_info.get('order_id')}")
            print(f"  task_status: {order_info.get('task_status')}")
            print(f"  budget: {order_info.get('budget')}")
            print(f"  order_create_time: {order_info.get('order_create_time')}")
            print(f"  delivery_start_time: {order_info.get('delivery_start_time')}")
            print(f"  delivery_end_time: {order_info.get('delivery_end_time')}")
            print(f"  task_start_time: {order_info.get('task_start_time')}")
            print(f"  task_end_time: {order_info.get('task_end_time')}")
            
        else:
            print("❌ 没有找到订单")
            
    finally:
        client.close()
        
finally:
    db.close()
