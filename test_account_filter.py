#!/usr/bin/env python3
"""测试单账号筛选时的API响应"""

import sys
sys.path.insert(0, '/opt/douplus/douplus-sync-python')

from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=" * 60)
print("测试1: stats_api.py - 全部账号统计（带accountId筛选）")
print("=" * 60)

# 测试 /stats/all 接口的SQL（accountId=2, period=all）
stats_sql = text("""
    SELECT 
        COALESCE(SUM(COALESCE(s.stat_cost, 0)), 0) as total_cost,
        COALESCE(SUM(COALESCE(s.total_play, 0)), 0) as total_play,
        COALESCE(SUM(COALESCE(s.custom_like, 0)), 0) as total_like,
        COALESCE(SUM(COALESCE(s.dy_comment, 0)), 0) as total_comment,
        COALESCE(SUM(COALESCE(s.dy_share, 0)), 0) as total_share,
        COALESCE(SUM(COALESCE(s.dy_follow, 0)), 0) as total_follow,
        COALESCE(SUM(COALESCE(s.dp_target_convert_cnt, 0)), 0) as total_convert,
        COUNT(DISTINCT o.item_id) as video_count,
        COUNT(DISTINCT o.id) as order_count
    FROM douplus_order o
    INNER JOIN douyin_account a ON o.account_id = a.id
    LEFT JOIN (
        SELECT s1.order_id, s1.stat_cost, s1.total_play, s1.custom_like,
               s1.dy_comment, s1.dy_share, s1.dy_follow, s1.dp_target_convert_cnt
        FROM douplus_order_stats s1
        INNER JOIN (
            SELECT order_id, MAX(stat_time) as max_time
            FROM douplus_order_stats
            GROUP BY order_id
        ) s2 ON s1.order_id = s2.order_id AND s1.stat_time = s2.max_time
    ) s ON o.order_id = s.order_id
    WHERE o.user_id = :user_id 
      AND o.deleted = 0
      AND a.deleted = 0
      AND o.account_id = :account_id
""")

try:
    result = db.execute(stats_sql, {'user_id': 1, 'account_id': 2}).fetchone()
    print(f"✓ 查询成功")
    print(f"  消耗: {result[0]}")
    print(f"  播放量: {result[1]}")
    print(f"  订单数: {result[8]}")
    print(f"  数据类型: {type(result[0])}")
except Exception as e:
    print(f"✗ 查询失败: {e}")

print("\n" + "=" * 60)
print("测试2: query_api.py - 视频统计（带accountId筛选）")
print("=" * 60)

# 测试 /video/stats/all 接口的SQL（accountId=2, period=all）
video_sql = text("""
    SELECT 
        v.item_id,
        MAX(o.aweme_title) as title,
        MAX(o.aweme_cover) as cover,
        COUNT(DISTINCT o.order_id) as order_count,
        COALESCE(SUM(v.total_cost), 0) as total_cost,
        COALESCE(SUM(v.total_play), 0) as total_play
    FROM douplus_video_stats_agg v
    INNER JOIN douyin_account a ON v.account_id = a.id
    INNER JOIN douplus_order o ON v.item_id = o.item_id AND v.account_id = o.account_id
    WHERE v.user_id = :user_id 
      AND a.deleted = 0
      AND o.account_id = :account_id
    GROUP BY v.item_id
    LIMIT 5
""")

try:
    results = db.execute(video_sql, {'user_id': 1, 'account_id': 2}).fetchall()
    print(f"✓ 查询成功，返回 {len(results)} 个视频")
    for row in results:
        print(f"  视频ID: {row[0]}, 消耗: {row[4]}, 播放: {row[5]}")
except Exception as e:
    print(f"✗ 查询失败: {e}")

print("\n" + "=" * 60)
print("测试3: 检查account_id=2是否存在")
print("=" * 60)

account_sql = text("""
    SELECT id, nickname, douyin_id, deleted 
    FROM douyin_account 
    WHERE user_id = :user_id
""")

try:
    accounts = db.execute(account_sql, {'user_id': 1}).fetchall()
    print(f"✓ 用户的账号列表:")
    for acc in accounts:
        status = "已解绑" if acc[3] == 1 else "正常"
        print(f"  ID: {acc[0]}, 昵称: {acc[1]}, 抖音号: {acc[2]}, 状态: {status}")
except Exception as e:
    print(f"✗ 查询失败: {e}")

db.close()
print("\n测试完成！")
