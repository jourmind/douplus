#!/usr/bin/env python3
"""
批量更新现有订单的task_id字段

从抖音API重新获取订单数据，填充task_id字段
"""

import sys
import os

# 添加项目路径
project_path = '/opt/douplus/douplus-sync-python'
sys.path.insert(0, project_path)
os.chdir(project_path)

from app.models import SessionLocal, DouyinAccount, DouplusOrder
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
from datetime import datetime

def update_task_ids():
    """批量更新task_id"""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("批量更新订单task_id字段")
        print("=" * 80)
        
        # 获取所有账号
        accounts = db.query(DouyinAccount).filter(DouyinAccount.status == 1).all()
        print(f"\n找到{len(accounts)}个活跃账号")
        
        total_updated = 0
        
        for account in accounts:
            print(f"\n处理账号: {account.nickname} (ID: {account.id})")
            
            # 创建客户端
            access_token = decrypt_access_token(account.access_token)
            client = DouyinClient(access_token)
            
            try:
                # 获取订单列表（最近100条）
                orders = client.get_order_list(
                    aweme_sec_uid=account.aweme_sec_uid,
                    page=1,
                    page_size=100
                )
                
                print(f"  API返回{len(orders)}条订单")
                
                # 更新每个订单的task_id
                for order_data in orders:
                    order_info = order_data.get("order", {})
                    order_id = str(order_info.get("order_id"))
                    task_id = str(order_info.get("task_id"))
                    
                    if order_id and task_id:
                        # 在数据库中查找订单
                        db_order = db.query(DouplusOrder).filter(
                            DouplusOrder.order_id == order_id
                        ).first()
                        
                        if db_order:
                            # 更新task_id
                            db_order.task_id = task_id
                            db_order.update_time = datetime.now()
                            total_updated += 1
                
                db.commit()
                print(f"  ✓ 更新完成")
                
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                db.rollback()
            finally:
                client.close()
        
        print(f"\n" + "=" * 80)
        print(f"总共更新了{total_updated}条订单的task_id")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ 更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    update_task_ids()
