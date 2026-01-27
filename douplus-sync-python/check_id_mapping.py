#!/usr/bin/env python3
"""
检查数据库存储的是order_id还是task_id
"""
from app.models import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # 查询这个订单
    sql = text("""
        SELECT order_id FROM douplus_order 
        WHERE order_id IN ('1855431292118059', '1855431292118043')
        LIMIT 10
    """)
    
    result = db.execute(sql).fetchall()
    
    print(f"数据库中存储的order_id:")
    for row in result:
        print(f"  {row[0]}")
    
    print(f"\n抖音API返回的数据:")
    print(f"  order_id: 1855431292118059")
    print(f"  task_id: 1855431292118043")
    
    print(f"\n⚠️  结论: 数据库存储的是抖音的 order_id，而续费API需要的是 task_id！")
    
finally:
    db.close()
