#!/usr/bin/env python3
"""
验证task_id更新结果
"""

import sys
import os

# 添加项目路径
project_path = '/opt/douplus/douplus-sync-python'
sys.path.insert(0, project_path)
os.chdir(project_path)

from app.models import SessionLocal, DouplusOrder

# DOU+后台真实订单号（task_id）
REAL_TASK_IDS = [
    '1855548567381076',
    '1855548553415739',
    '1855548517984355',
    '1855548548789328',
    '1855548523186375',
]

def verify_task_ids():
    """验证task_id更新结果"""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("验证task_id更新结果")
        print("=" * 80)
        
        print(f"\n验证DOU+后台订单号是否可以查询:")
        print(f"{'DOU+后台订单号':<20} {'order_id':<20} {'创建时间':<20} {'状态'}")
        print("-" * 80)
        
        for task_id in REAL_TASK_IDS:
            order = db.query(DouplusOrder).filter(
                DouplusOrder.task_id == task_id
            ).first()
            
            if order:
                create_time = order.order_create_time.strftime("%Y-%m-%d %H:%M:%S") if order.order_create_time else ""
                print(f"{task_id:<20} {order.order_id:<20} {create_time:<20} ✓ 找到")
            else:
                print(f"{task_id:<20} {'无':<20} {'无':<20} ❌ 未找到")
        
        # 统计总体情况
        print(f"\n\n总体统计:")
        total = db.query(DouplusOrder).count()
        with_task_id = db.query(DouplusOrder).filter(DouplusOrder.task_id.isnot(None)).count()
        
        print(f"  订单总数: {total}")
        print(f"  有task_id的订单: {with_task_id}")
        print(f"  覆盖率: {with_task_id/total*100:.1f}%")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    verify_task_ids()
