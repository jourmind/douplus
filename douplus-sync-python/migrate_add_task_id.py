#!/usr/bin/env python3
"""
执行数据库迁移：添加task_id字段
"""
from app.models import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("正在添加task_id字段...")
    
    # 检查字段是否存在
    check_sql = text("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'douplus' 
        AND TABLE_NAME = 'douplus_order' 
        AND COLUMN_NAME = 'task_id'
    """)
    
    result = db.execute(check_sql).scalar()
    
    if result > 0:
        print("✅ task_id字段已存在，跳过添加")
    else:
        # 添加字段（分两步）
        add_column_sql = text("ALTER TABLE douplus_order ADD COLUMN task_id VARCHAR(64) NULL AFTER order_id")
        db.execute(add_column_sql)
        db.commit()
        print("✅ task_id字段添加成功！")
        
        # 添加索引
        add_index_sql = text("ALTER TABLE douplus_order ADD INDEX idx_task_id (task_id)")
        db.execute(add_index_sql)
        db.commit()
        print("✅ task_id索引添加成功！")
    
finally:
    db.close()
