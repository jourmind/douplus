#!/usr/bin/env python3
"""
测试订单效果数据
检查数据库中是否有效果数据
"""
from app.models import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # 1. 检查订单表
    print("=" * 80)
    print("【步骤1】检查订单表数据")
    print("=" * 80)
    
    order_sql = text("""
        SELECT order_id, status, budget, aweme_title, order_create_time
        FROM douplus_order
        WHERE deleted = 0
        ORDER BY order_create_time DESC
        LIMIT 5
    """)
    
    orders = db.execute(order_sql).fetchall()
    print(f"\n找到 {len(orders)} 个订单:")
    for order in orders:
        print(f"  订单ID: {order[0]}, 状态: {order[1]}, 预算: {order[2]}元, 创建时间: {order[4]}")
    
    if not orders:
        print("⚠️  订单表为空！")
        exit(1)
    
    # 取第一个订单ID
    test_order_id = orders[0][0]
    
    # 2. 检查效果数据表
    print(f"\n{'=' * 80}")
    print(f"【步骤2】检查订单 {test_order_id} 的效果数据")
    print("=" * 80)
    
    stats_sql = text("""
        SELECT order_id, stat_time, stat_cost, total_play, custom_like, 
               dy_comment, dy_share, dp_target_convert_cnt, custom_convert_cost
        FROM douplus_order_stats
        WHERE order_id = :order_id
        ORDER BY stat_time DESC
        LIMIT 5
    """)
    
    stats = db.execute(stats_sql, {'order_id': test_order_id}).fetchall()
    
    if stats:
        print(f"\n✅ 找到 {len(stats)} 条效果数据:")
        for stat in stats:
            print(f"  时间: {stat[1]}, 消耗: {stat[2]}元, 播放: {stat[3]}, 点赞: {stat[4]}, 转化: {stat[7]}")
    else:
        print(f"\n❌ 订单 {test_order_id} 没有效果数据！")
    
    # 3. 检查所有订单的效果数据统计
    print(f"\n{'=' * 80}")
    print("【步骤3】检查效果数据表统计")
    print("=" * 80)
    
    count_sql = text("""
        SELECT 
            COUNT(DISTINCT order_id) as order_count,
            COUNT(*) as stats_count,
            MIN(stat_time) as min_time,
            MAX(stat_time) as max_time
        FROM douplus_order_stats
    """)
    
    result = db.execute(count_sql).fetchone()
    print(f"\n订单数: {result[0]}")
    print(f"效果数据记录数: {result[1]}")
    print(f"最早数据时间: {result[2]}")
    print(f"最新数据时间: {result[3]}")
    
    if result[1] == 0:
        print("\n❌ 效果数据表是空的！需要同步数据。")
    
    # 4. 检查前端查询的字段
    print(f"\n{'=' * 80}")
    print("【步骤4】模拟前端查询（检查字段映射）")
    print("=" * 80)
    
    frontend_sql = text("""
        SELECT 
            o.order_id,
            o.budget,
            COALESCE(SUM(s.stat_cost), 0) as total_cost,
            COALESCE(SUM(s.total_play), 0) as total_play,
            COALESCE(SUM(s.custom_like), 0) as total_like,
            COALESCE(SUM(s.dy_share), 0) as total_share,
            COALESCE(SUM(s.dp_target_convert_cnt), 0) as total_convert
        FROM douplus_order o
        LEFT JOIN douplus_order_stats s ON o.order_id = s.order_id
        WHERE o.deleted = 0
        GROUP BY o.order_id
        ORDER BY o.order_create_time DESC
        LIMIT 5
    """)
    
    results = db.execute(frontend_sql).fetchall()
    print(f"\n查询结果:")
    for row in results:
        print(f"  订单: {row[0]}, 预算: {row[1]}元, 消耗: {row[2]}元, 播放: {row[3]}, 点赞: {row[4]}, 转化: {row[6]}")
    
    print(f"\n{'=' * 80}")
    print("排查完成")
    print("=" * 80)
    
finally:
    db.close()
