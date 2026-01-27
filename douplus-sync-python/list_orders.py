#!/usr/bin/env python3
"""
查询所有投放中的订单
"""
from app.models import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # 查询所有投放中的订单
    order_sql = text("""
        SELECT o.order_id, o.item_id, o.status, o.budget, o.duration,
               o.aweme_title, a.nickname
        FROM douplus_order o
        INNER JOIN douyin_account a ON o.account_id = a.id
        WHERE o.status = 'DELIVERING' AND o.deleted = 0
        ORDER BY o.order_create_time DESC
        LIMIT 10
    """)
    
    orders = db.execute(order_sql).fetchall()
    
    print(f"\n找到 {len(orders)} 个投放中的订单:\n")
    print(f"{'订单ID':<20} {'状态':<12} {'预算':<8} {'时长':<8} {'账号':<20} {'视频标题':<30}")
    print("=" * 120)
    
    for order in orders:
        order_id, item_id, status, budget, duration, title, nickname = order
        print(f"{order_id:<20} {status:<12} {budget:<8.0f} {duration:<8} {nickname or 'N/A':<20} {(title or 'N/A')[:30]}")
    
finally:
    db.close()
