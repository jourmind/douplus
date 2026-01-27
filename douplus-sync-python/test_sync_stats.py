#!/usr/bin/env python3
"""
测试效果数据同步
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token

db = SessionLocal()

try:
    # 获取第一个账号
    account = db.query(DouyinAccount).filter_by(deleted=0).first()
    
    if not account:
        print("❌ 没有找到账号")
        exit(1)
    
    print(f"✅ 使用账号: {account.nickname} (ID: {account.id})")
    print(f"   aweme_sec_uid: {account.aweme_sec_uid}\n")
    
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
        
        if not order_list:
            print("❌ 没有订单")
            exit(1)
        
        print(f"✅ 找到 {len(order_list)} 个订单\n")
        
        # 取第一个投放中的订单
        delivering_order = None
        for order_data in order_list:
            if order_data.get("order", {}).get("task_status") == "DELIVERING":
                delivering_order = order_data
                break
        
        if not delivering_order:
            print("⚠️  没有找到投放中的订单，使用第一个订单测试")
            delivering_order = order_list[0]
        
        order_info = delivering_order.get("order", {})
        task_id = order_info.get("task_id")
        order_id = order_info.get("order_id")
        status = order_info.get("task_status")
        
        print(f"测试订单:")
        print(f"  order_id: {order_id}")
        print(f"  task_id: {task_id}")
        print(f"  status: {status}\n")
        
        # 查询效果数据
        print(f"正在查询订单 {task_id} 的效果数据...")
        
        try:
            stats_data = client.get_order_stats(
                task_id=task_id,
                aweme_sec_uid=account.aweme_sec_uid
            )
            
            print(f"\n✅ 抖音API返回的效果数据:")
            print(f"  返回数据: {stats_data}\n")
            
            if stats_data:
                print("✅ 效果数据同步API正常！")
            else:
                print("⚠️  API返回数据为空")
                
        except Exception as e:
            print(f"❌ 查询效果数据失败: {e}")
            
    finally:
        client.close()
        
finally:
    db.close()
