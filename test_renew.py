#!/usr/bin/env python3
"""
测试续费功能
订单ID: 1855431230726176
金额: 100元
时长: 720小时
"""
import sys
sys.path.insert(0, '/opt/douplus/douplus-sync-python')

from app.database import SessionLocal
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
from sqlalchemy import text

print("=" * 60)
print("开始测试续费功能")
print("=" * 60)

# 订单信息
order_id = '1855431230726176'
budget = 100  # 元
duration = 720  # 小时

db = SessionLocal()

try:
    # 1. 查询订单信息
    print(f"\n[步骤1] 查询订单信息...")
    order_sql = text("""
        SELECT o.id, o.order_id, o.account_id, o.status, o.item_id,
               a.aweme_sec_uid, a.open_id, a.access_token
        FROM douplus_order o
        INNER JOIN douyin_account a ON o.account_id = a.id
        WHERE o.order_id = :order_id AND o.deleted = 0
    """)
    
    order = db.execute(order_sql, {'order_id': order_id}).fetchone()
    
    if not order:
        print(f"❌ 错误：订单不存在！order_id={order_id}")
        sys.exit(1)
    
    internal_id, task_id, account_id, status, item_id, aweme_sec_uid, open_id, token_encrypted = order
    
    print(f"✅ 订单查询成功:")
    print(f"   - 内部ID: {internal_id}")
    print(f"   - 订单ID(task_id): {task_id}")
    print(f"   - 账号ID: {account_id}")
    print(f"   - 视频ID(item_id): {item_id}")
    print(f"   - 订单状态: {status}")
    print(f"   - aweme_sec_uid: {aweme_sec_uid}")
    print(f"   - open_id: {open_id}")
    
    # 2. 检查订单状态
    print(f"\n[步骤2] 检查订单状态...")
    if status not in ['DELIVERING', 'RUNNING']:
        print(f"❌ 错误：订单状态为 {status}，不允许续费（需要DELIVERING或RUNNING）")
        sys.exit(1)
    print(f"✅ 订单状态正常: {status}")
    
    # 3. 解密access_token
    print(f"\n[步骤3] 解密access_token...")
    access_token = decrypt_access_token(token_encrypted)
    print(f"✅ access_token解密成功: {access_token[:20]}...")
    
    # 4. 调用续费API
    print(f"\n[步骤4] 调用抖音续费API...")
    print(f"   - task_id: {task_id}")
    print(f"   - aweme_sec_uid: {aweme_sec_uid}")
    print(f"   - budget: {budget}元 ({budget * 100}分)")
    print(f"   - duration: {duration}小时")
    
    client = DouyinClient(
        access_token=access_token,
        open_id=open_id
    )
    
    try:
        result = client.renew_order(
            task_id=task_id,
            aweme_sec_uid=aweme_sec_uid,
            renewal_budget=budget * 100,  # 转换为分
            renewal_delivery_hour=duration
        )
        
        print(f"\n{'=' * 60}")
        print(f"✅ 续费成功！")
        print(f"{'=' * 60}")
        print(f"返回数据: {result}")
        
    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"❌ 续费失败！")
        print(f"{'=' * 60}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 分析错误原因
        error_msg = str(e)
        if 'record not found' in error_msg:
            print(f"\n⚠️  分析: 抖音平台找不到此订单记录")
            print(f"   可能原因:")
            print(f"   1. 订单在抖音平台已结束/取消")
            print(f"   2. 订单ID不正确")
            print(f"   3. aweme_sec_uid不匹配")
        elif 'must be at least 10000' in error_msg:
            print(f"\n⚠️  分析: 金额不符合要求（最低100元）")
        elif 'code=50000' in error_msg:
            print(f"\n⚠️  分析: 抖音服务器临时错误")
        
        sys.exit(1)
    finally:
        client.close()

finally:
    db.close()

print(f"\n{'=' * 60}")
print("测试完成")
print(f"{'=' * 60}")
