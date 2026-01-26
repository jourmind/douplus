"""
初始化视频预聚合表

说明：
1. 这是一个临时过渡方案
2. 因为当前数据在 douplus_task 表（旧表），需要先迁移到新表
3. 暂时从 douplus_task 表聚合数据到 douplus_video_stats_agg

执行方式：
python3 init_video_agg.py
"""
from sqlalchemy import text
from datetime import datetime
from loguru import logger
from app.models import get_db
from app.utils.time_window import get_current_window

def init_video_agg_from_old_table():
    """
    临时方案：从douplus_task表聚合到douplus_video_stats_agg
    
    注意：这是过渡方案，正式流程应该是：
    douplus_order → douplus_order_stats → douplus_video_stats_agg
    """
    db = get_db()
    try:
        logger.info("开始从douplus_task表初始化视频预聚合数据")
        
        # 使用当前时间窗口
        current_window = get_current_window()
        
        # 从douplus_task聚合到douplus_video_stats_agg
        sql = text("""
            INSERT INTO douplus_video_stats_agg (
                item_id, account_id, user_id, stat_time,
                order_count, total_budget, total_cost,
                total_play, total_like, total_comment, total_share, total_follow,
                total_convert, total_home_visited,
                avg_5s_rank, avg_convert_cost,
                play_per_100_cost, like_rate, share_rate, share_per_100_play,
                agg_time, data_version,
                create_time, update_time
            )
            SELECT 
                item_id,
                account_id,
                user_id,
                :stat_time as stat_time,
                
                -- 基础统计
                COUNT(DISTINCT order_id) as order_count,
                SUM(budget) as total_budget,
                SUM(actual_cost) as total_cost,
                
                -- 效果指标
                SUM(play_count) as total_play,
                SUM(like_count) as total_like,
                SUM(comment_count) as total_comment,
                SUM(share_count) as total_share,
                SUM(follow_count) as total_follow,
                SUM(dp_target_convert_cnt) as total_convert,
                SUM(dy_home_visited) as total_home_visited,
                
                -- 平均指标
                AVG(play_duration_5s_rank) as avg_5s_rank,
                AVG(custom_convert_cost) as avg_convert_cost,
                
                -- 计算指标（百播放量 = 播放量 / 消耗 * 100）
                CASE 
                    WHEN SUM(actual_cost) > 0 
                    THEN SUM(play_count) / SUM(actual_cost) * 100
                    ELSE 0 
                END as play_per_100_cost,
                
                -- 点赞率 = 点赞数 / 播放量
                CASE 
                    WHEN SUM(play_count) > 0 
                    THEN SUM(like_count) * 1.0 / SUM(play_count)
                    ELSE 0 
                END as like_rate,
                
                -- 转发率 = 转发数 / 播放量
                CASE 
                    WHEN SUM(play_count) > 0 
                    THEN SUM(share_count) * 1.0 / SUM(play_count)
                    ELSE 0 
                END as share_rate,
                
                -- 百转发率 = 转发数 / 播放量 * 100
                CASE 
                    WHEN SUM(play_count) > 0 
                    THEN SUM(share_count) / SUM(play_count) * 100
                    ELSE 0 
                END as share_per_100_play,
                
                NOW() as agg_time,
                1 as data_version,
                NOW() as create_time,
                NOW() as update_time
                
            FROM douplus_task
            WHERE deleted = 0 
              AND item_id IS NOT NULL
              AND item_id != ''
            GROUP BY item_id, account_id, user_id
            
            ON DUPLICATE KEY UPDATE
                order_count = VALUES(order_count),
                total_budget = VALUES(total_budget),
                total_cost = VALUES(total_cost),
                total_play = VALUES(total_play),
                total_like = VALUES(total_like),
                total_comment = VALUES(total_comment),
                total_share = VALUES(total_share),
                total_follow = VALUES(total_follow),
                total_convert = VALUES(total_convert),
                total_home_visited = VALUES(total_home_visited),
                avg_5s_rank = VALUES(avg_5s_rank),
                avg_convert_cost = VALUES(avg_convert_cost),
                play_per_100_cost = VALUES(play_per_100_cost),
                like_rate = VALUES(like_rate),
                share_rate = VALUES(share_rate),
                share_per_100_play = VALUES(share_per_100_play),
                agg_time = NOW(),
                data_version = data_version + 1,
                update_time = NOW()
        """)
        
        result = db.execute(sql, {'stat_time': current_window})
        db.commit()
        
        affected_rows = result.rowcount
        logger.info(f"视频预聚合表初始化完成: 聚合了{affected_rows}个视频")
        
        # 查询统计
        count_result = db.execute(text("""
            SELECT COUNT(*) as total, 
                   SUM(order_count) as total_orders,
                   SUM(total_play) as total_plays
            FROM douplus_video_stats_agg
        """)).fetchone()
        
        logger.info(f"当前预聚合表统计: {count_result[0]}个视频, {count_result[1]}个订单, {count_result[2]}次播放")
        
        return affected_rows
        
    except Exception as e:
        logger.error(f"初始化视频预聚合表失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/opt/douplus/douplus-sync-python')
    
    print("=" * 60)
    print("初始化视频预聚合表")
    print("=" * 60)
    print()
    
    try:
        count = init_video_agg_from_old_table()
        print()
        print(f"✅ 成功! 聚合了 {count} 个视频的数据")
        print()
        print("说明：")
        print("1. 这是从 douplus_task 旧表临时聚合的数据")
        print("2. 后续会改为从 douplus_order → douplus_order_stats → douplus_video_stats_agg 的正规流程")
        print("3. 现在前端查询订单列表应该可以看到效果数据了")
        print()
    except Exception as e:
        print()
        print(f"❌ 失败: {e}")
        print()
        sys.exit(1)
