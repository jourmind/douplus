#!/usr/bin/env python3
"""
手动触发效果数据同步
将抖音后台的投放效果数据同步到 douplus_video_stats_agg 表
"""

import sys
from datetime import datetime
from app.tasks.stats_sync import sync_single_account_stats
from app.models import SessionLocal, DouyinAccount
from sqlalchemy import text

print("=" * 80)
print("手动触发效果数据同步")
print("=" * 80)

# 1. 获取所有账号
print("\n【1】获取已授权账号列表")
print("-" * 80)

db = SessionLocal()
try:
    accounts = db.query(DouyinAccount).filter(
        DouyinAccount.deleted == 0,
        DouyinAccount.status == 1
    ).all()
    
    print(f"找到 {len(accounts)} 个已授权账号:")
    for acc in accounts:
        print(f"  - ID: {acc.id}, Nickname: {acc.nickname}, AdvertiserId: {acc.advertiser_id}")
    
    if not accounts:
        print("⚠️  没有找到已授权账号，无法同步")
        sys.exit(0)
    
finally:
    db.close()

# 2. 开始同步每个账号的效果数据
print("\n【2】开始同步效果数据")
print("-" * 80)

success_count = 0
error_count = 0

for acc in accounts:
    print(f"\n同步账号: {acc.nickname} (ID: {acc.id})")
    try:
        # 调用Celery任务函数（直接执行，不通过队列）
        result = sync_single_account_stats(acc.id)
        
        print(f"  ✅ 同步完成")
        success_count += 1
            
    except Exception as e:
        print(f"  ❌ 同步异常: {str(e)}")
        error_count += 1

# 3. 验证同步结果
print("\n【3】验证同步结果")
print("-" * 80)

db = SessionLocal()
try:
    # 检查投放中订单的效果数据
    query = text("""
        SELECT 
            o.order_id,
            o.item_id,
            COUNT(s.id) as stats_count,
            MAX(s.stat_time) as latest_stat_time
        FROM douplus_order o
        LEFT JOIN douplus_video_stats_agg s ON o.item_id = s.item_id
        WHERE o.status = 'DELIVERING'
        GROUP BY o.order_id, o.item_id
        LIMIT 10
    """)
    
    results = db.execute(query).fetchall()
    
    print(f"投放中订单效果数据统计:")
    print()
    
    has_data_count = 0
    no_data_count = 0
    
    for row in results:
        if row[2] > 0:
            print(f"✅ 订单 {row[0]}: 有效果数据 ({row[2]}条记录, 最新: {row[3]})")
            has_data_count += 1
        else:
            print(f"❌ 订单 {row[0]}: 无效果数据")
            no_data_count += 1
    
    print()
    print(f"统计: {has_data_count}个订单有数据, {no_data_count}个订单无数据")
    
finally:
    db.close()

# 4. 总结
print("\n" + "=" * 80)
print("同步完成")
print("=" * 80)
print(f"成功: {success_count}个账号")
print(f"失败: {error_count}个账号")

if has_data_count > 0:
    print(f"\n✅ 效果数据已同步，请刷新前端页面查看")
else:
    print(f"\n⚠️  同步后仍无效果数据，可能原因:")
    print("  1. 抖音后台该订单确实还没有效果数据")
    print("  2. 订单刚创建，数据还在统计中")
    print("  3. API接口返回数据格式有问题")
print("=" * 80)
