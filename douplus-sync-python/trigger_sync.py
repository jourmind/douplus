#!/usr/bin/env python3
"""
手动触发效果数据同步，并写入数据库
"""
from app.models import SessionLocal, DouyinAccount, DouplusOrder, DouplusOrderStats
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
from datetime import datetime, timedelta
from sqlalchemy.dialects.mysql import insert

db = SessionLocal()

try:
    # 获取所有账号
    accounts = db.query(DouyinAccount).filter_by(deleted=0).all()
    
    print(f"找到 {len(accounts)} 个账号\n")
    
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
                # 查询最近7天的效果数据
                begin_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                end_time = datetime.now().strftime('%Y-%m-%d')
                
                print(f"查询时间范围: {begin_time} ~ {end_time}")
                
                stats_data = client.get_order_report(
                    aweme_sec_uid=account.aweme_sec_uid,
                    begin_time=begin_time,
                    end_time=end_time
                )
                
                if not stats_data:
                    print("⚠️  没有效果数据\n")
                    continue
                
                print(f"✅ 获取到 {len(stats_data)} 条效果数据")
                
                # 统计时间（使用当前时间）
                stat_time = datetime.now()
                
                # 保存到数据库
                saved_count = 0
                for order_id, stats in stats_data.items():
                    try:
                        # item_id必填，如果API没返回就从订单表查询
                        item_id = stats.get('item_id')
                        if not item_id:
                            order = db.query(DouplusOrder).filter_by(order_id=order_id).first()
                            if order:
                                item_id = order.item_id
                            else:
                                item_id = ''  # 兜底值
                        
                        # 构建数据
                        data = {
                            'order_id': order_id,
                            'item_id': item_id,
                            'stat_time': stat_time,
                            'stat_cost': stats['stat_cost'],
                            'total_play': stats['total_play'],
                            'custom_like': stats['custom_like'],
                            'dy_comment': stats['dy_comment'],
                            'dy_share': stats['dy_share'],
                            'dy_follow': stats['dy_follow'],
                            'play_duration_5s_rank': stats['play_duration_5s_rank'],
                            'dy_home_visited': stats['dy_home_visited'],
                            'dp_target_convert_cnt': stats['dp_target_convert_cnt'],
                            'custom_convert_cost': stats['custom_convert_cost'],
                            'show_cnt': stats['show_cnt'],
                            'live_click_source_cnt': stats['live_click_source_cnt'],
                            'live_gift_uv': stats['live_gift_uv'],
                            'live_gift_amount': stats['live_gift_amount'],
                            'live_comment_cnt': stats['live_comment_cnt'],
                            'live_follow_count': stats['live_follow_count'],
                            'live_gift_cnt': stats['live_gift_cnt'],
                            'update_time': datetime.now()
                        }
                        
                        # 使用INSERT ... ON DUPLICATE KEY UPDATE
                        stmt = insert(DouplusOrderStats).values(data)
                        stmt = stmt.on_duplicate_key_update(**data)
                        
                        db.execute(stmt)
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"  ❌ 保存订单 {order_id} 失败: {e}")
                
                db.commit()
                print(f"✅ 成功保存 {saved_count} 条效果数据\n")
                
            finally:
                client.close()
                
        except Exception as e:
            print(f"❌ 同步失败: {e}\n")
            db.rollback()
    
    print(f"{'='*80}")
    print("同步完成")
    print(f"{'='*80}")
    
finally:
    db.close()
