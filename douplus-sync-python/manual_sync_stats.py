#!/usr/bin/env python3
"""
手动同步效果数据
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
from datetime import datetime, timedelta
from sqlalchemy import text

db = SessionLocal()

try:
    # 获取所有账号
    accounts = db.query(DouyinAccount).filter_by(deleted=0).all()
    
    print(f"找到 {len(accounts)} 个账号\n")
    
    # 设置同步时间范围（最近7天）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"同步时间范围: {start_date} 到 {end_date}\n")
    
    for account in accounts:
        print(f"{'='*80}")
        print(f"账号: {account.nickname} (ID: {account.id})")
        print(f"{'='*80}")
        
        try:
            # 解密token
            access_token = decrypt_access_token(account.access_token)
            
            # 创建客户端
            client = DouyinClient(access_token=access_token)
            
            try:
                # 获取效果数据
                print(f"正在查询效果数据...")
                stats_data = client.get_order_report(
                    aweme_sec_uid=account.aweme_sec_uid,
                    begin_time=start_date,
                    end_time=end_date
                )
                
                if stats_data:
                    print(f"✅ 获取到 {len(stats_data)} 个订单的效果数据")
                    
                    # 显示前5个订单的数据
                    for i, (order_id, stats) in enumerate(list(stats_data.items())[:5]):
                        print(f"  订单 {order_id}: 播放{stats['total_play']}, 消耗{stats['stat_cost']}元")
                    
                    if len(stats_data) > 5:
                        print(f"  ... 还有 {len(stats_data) - 5} 个订单")
                else:
                    print(f"⚠️  没有效果数据")
                    
            finally:
                client.close()
                
        except Exception as e:
            print(f"❌ 同步失败: {e}")
        
        print()
    
    print(f"\n{'='*80}")
    print("同步完成")
    print(f"{'='*80}")
    
finally:
    db.close()
