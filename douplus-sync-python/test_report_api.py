#!/usr/bin/env python3
"""
测试效果报告API - 查询昨天的数据
"""
from app.models import SessionLocal, DouyinAccount
from app.douyin_client import DouyinClient
from app.utils.crypto import decrypt_access_token
from datetime import datetime, timedelta

db = SessionLocal()

try:
    # 获取第一个账号
    account = db.query(DouyinAccount).filter_by(deleted=0).first()
    
    print(f"账号: {account.nickname}")
    print(f"aweme_sec_uid: {account.aweme_sec_uid}\n")
    
    # 解密token
    access_token = decrypt_access_token(account.access_token)
    
    # 创建客户端
    client = DouyinClient(access_token=access_token)
    
    try:
        # 测试不同的时间范围
        test_cases = [
            {
                "name": "最近1天",
                "begin": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            },
            {
                "name": "最近3天",
                "begin": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            },
            {
                "name": "最近7天",
                "begin": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            },
        ]
        
        for case in test_cases:
            print(f"{'='*80}")
            print(f"测试: {case['name']} ({case['begin']} ~ {case['end']})")
            print(f"{'='*80}")
            
            try:
                stats_data = client.get_order_report(
                    aweme_sec_uid=account.aweme_sec_uid,
                    begin_time=case['begin'],
                    end_time=case['end']
                )
                
                if stats_data:
                    print(f"✅ 获取到 {len(stats_data)} 条效果数据\n")
                    
                    # 显示前3条
                    for i, (order_id, stats) in enumerate(list(stats_data.items())[:3]):
                        print(f"订单 {order_id}:")
                        print(f"  消耗: {stats['stat_cost']}元")
                        print(f"  播放: {stats['total_play']}")
                        print(f"  点赞: {stats['custom_like']}")
                        print(f"  转化: {stats['dp_target_convert_cnt']}")
                    
                    if len(stats_data) > 3:
                        print(f"... 还有 {len(stats_data) - 3} 条")
                else:
                    print("⚠️  没有数据")
                    
            except Exception as e:
                print(f"❌ 查询失败: {e}")
            
            print()
        
    finally:
        client.close()
        
finally:
    db.close()
