#!/usr/bin/env python3
"""
检查订单的时间信息
"""
from app.models import SessionLocal
from sqlalchemy import text
from datetime import datetime

db = SessionLocal()

try:
    order_sql = text("""
        SELECT o.order_id, o.status, o.budget, o.duration,
               o.order_create_time, o.order_start_time, o.order_end_time,
               o.last_sync_time
        FROM douplus_order o
        WHERE o.order_id = '1855431292118059' AND o.deleted = 0
    """)
    
    order = db.execute(order_sql).fetchone()
    
    if order:
        order_id, status, budget, duration, create_time, start_time, end_time, sync_time = order
        
        print(f"\n订单详情:")
        print(f"  订单ID: {order_id}")
        print(f"  状态: {status}")
        print(f"  预算: {budget}元")
        print(f"  时长: {duration}小时")
        print(f"  创建时间: {create_time}")
        print(f"  开始时间: {start_time}")
        print(f"  结束时间: {end_time}")
        print(f"  最后同步: {sync_time}")
        
        now = datetime.now()
        if end_time:
            if end_time < now:
                print(f"\n⚠️  订单已过期！结束时间是 {end_time}，当前时间是 {now}")
            else:
                remaining = end_time - now
                print(f"\n✅ 订单还有 {remaining} 剩余")
        else:
            print(f"\n⚠️  订单没有结束时间")
        
    else:
        print("订单不存在")
        
finally:
    db.close()
