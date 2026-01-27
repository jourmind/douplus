#!/usr/bin/env python3
"""
从抖音API查找未续费过的投放中订单
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token

db = SessionLocal()

try:
    # 获取账号ID=5
    account = db.query(DouyinAccount).filter_by(id=5, deleted=0).first()
    
    if not account:
        print("❌ 没有找到账号")
        exit(1)
    
    print(f"✅ 使用账号: {account.nickname} (ID: {account.id})\n")
    
    access_token = decrypt_access_token(account.access_token)
    client = DouyinClient(access_token=access_token)
    
    try:
        # 查询订单列表
        result = client.get_order_list(
            aweme_sec_uid=account.aweme_sec_uid,
            page=1,
            page_size=50
        )
        
        if result:
            print(f"找到 {len(result)} 个订单\n")
            print(f"{'订单ID':<20} {'状态':<15} {'预算':<8} {'续费次数':<10} {'创建时间':<20}")
            print("=" * 85)
            
            # 找未续费过的投放中订单
            target_orders = []
            for order_data in result:
                order_info = order_data.get("order", {})
                order_id = order_info.get("order_id")
                status = order_info.get("task_status")
                budget = order_info.get("budget", 0) / 100.0
                renew_count = order_info.get("renew_count", 0)
                create_time = order_info.get("order_create_time")
                
                print(f"{order_id:<20} {status:<15} {budget:<8.0f} {renew_count:<10} {create_time:<20}")
                
                if status == "DELIVERING" and renew_count == 0:
                    target_orders.append(order_id)
            
            if target_orders:
                print(f"\n✅ 找到 {len(target_orders)} 个未续费过的投放中订单:")
                for order_id in target_orders:
                    print(f"   - {order_id}")
            else:
                print(f"\n⚠️  没有找到未续费过的投放中订单")
        else:
            print("❌ 没有找到订单")
            
    finally:
        client.close()
        
finally:
    db.close()
