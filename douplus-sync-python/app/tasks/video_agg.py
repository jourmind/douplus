"""
视频维度效果数据聚合任务

功能：从 douplus_order_stats 聚合到 douplus_video_stats_agg
策略：按 item_id + stat_time 聚合多个订单的效果数据
更新频率：每5分钟
"""
from celery import Task
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.dialects.mysql import insert
from loguru import logger

from app.models import (
    DouplusOrder, 
    DouplusOrderStats, 
    DouplusVideoStatsAgg,
    get_db
)
from app.utils.time_window import get_current_window
from app.config import get_settings


settings = get_settings()


class VideoAggTask(Task):
    """视频维度聚合任务基类"""
    
    def aggregate_video_stats(self, stat_time: datetime = None):
        """
        聚合视频维度效果数据
        
        Args:
            stat_time: 统计时间窗口，默认为当前窗口
        """
        if stat_time is None:
            stat_time = get_current_window()
        
        db = get_db()
        try:
            logger.info(f"开始聚合视频数据: stat_time={stat_time}")
            
            # 使用SQL直接聚合，避免ORM性能问题
            agg_sql = text("""
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
                    o.item_id,
                    o.account_id,
                    o.user_id,
                    :stat_time as stat_time,
                    
                    -- 基础统计
                    COUNT(DISTINCT o.order_id) as order_count,
                    SUM(o.budget) as total_budget,
                    SUM(s.stat_cost) as total_cost,
                    
                    -- 效果指标
                    SUM(s.total_play) as total_play,
                    SUM(s.custom_like) as total_like,
                    SUM(s.dy_comment) as total_comment,
                    SUM(s.dy_share) as total_share,
                    SUM(s.dy_follow) as total_follow,
                    SUM(s.dp_target_convert_cnt) as total_convert,
                    SUM(s.dy_home_visited) as total_home_visited,
                    
                    -- 平均指标
                    AVG(s.play_duration_5s_rank) as avg_5s_rank,
                    AVG(s.custom_convert_cost) as avg_convert_cost,
                    
                    -- 计算指标（百播放量 = 播放量 / 消耗 * 100）
                    CASE 
                        WHEN SUM(s.stat_cost) > 0 
                        THEN SUM(s.total_play) / SUM(s.stat_cost) * 100
                        ELSE 0 
                    END as play_per_100_cost,
                    
                    -- 点赞率 = 点赞数 / 播放量
                    CASE 
                        WHEN SUM(s.total_play) > 0 
                        THEN SUM(s.custom_like) * 1.0 / SUM(s.total_play)
                        ELSE 0 
                    END as like_rate,
                    
                    -- 转发率 = 转发数 / 播放量
                    CASE 
                        WHEN SUM(s.total_play) > 0 
                        THEN SUM(s.dy_share) * 1.0 / SUM(s.total_play)
                        ELSE 0 
                    END as share_rate,
                    
                    -- 百转发率 = 转发数 / 播放量 * 100
                    CASE 
                        WHEN SUM(s.total_play) > 0 
                        THEN SUM(s.dy_share) / SUM(s.total_play) * 100
                        ELSE 0 
                    END as share_per_100_play,
                    
                    NOW() as agg_time,
                    1 as data_version,
                    NOW() as create_time,
                    NOW() as update_time
                    
                FROM douplus_order o
                INNER JOIN douplus_order_stats s 
                    ON o.order_id = s.order_id AND s.stat_time = :stat_time
                WHERE o.deleted = 0
                GROUP BY o.item_id, o.account_id, o.user_id
                
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
            
            result = db.execute(agg_sql, {'stat_time': stat_time})
            db.commit()
            
            affected_rows = result.rowcount
            logger.info(f"视频数据聚合完成: stat_time={stat_time}, 聚合了{affected_rows}个视频")
            
            return affected_rows
            
        except Exception as e:
            logger.error(f"视频数据聚合失败: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
    
    def aggregate_recent_windows(self, window_count: int = 12):
        """
        聚合最近N个时间窗口的数据
        
        Args:
            window_count: 窗口数量，默认12（即1小时，5分钟一个窗口）
        """
        current_window = get_current_window()
        
        for i in range(window_count):
            stat_time = current_window - timedelta(minutes=5 * i)
            try:
                self.aggregate_video_stats(stat_time)
            except Exception as e:
                logger.error(f"聚合窗口{stat_time}失败: {e}")


def aggregate_current_window():
    """
    聚合当前时间窗口的视频数据
    
    由Celery Beat每5分钟调用一次
    """
    task = VideoAggTask()
    task.aggregate_video_stats()


def aggregate_all_recent():
    """
    聚合最近1小时的所有窗口数据
    
    用于数据修复或初始化
    """
    logger.info("开始聚合最近1小时的视频数据")
    task = VideoAggTask()
    task.aggregate_recent_windows(window_count=12)
    logger.info("聚合完成")


def rebuild_video_agg_table():
    """
    重建整个视频预聚合表
    
    警告：此操作会重新计算所有历史数据，耗时较长
    仅用于数据迁移或表损坏修复
    """
    db = get_db()
    try:
        logger.warning("开始重建视频预聚合表（清空并重新计算所有数据）")
        
        # 1. 清空表
        db.execute(text("TRUNCATE TABLE douplus_video_stats_agg"))
        db.commit()
        logger.info("已清空 douplus_video_stats_agg 表")
        
        # 2. 获取所有不同的stat_time
        result = db.execute(text("""
            SELECT DISTINCT stat_time 
            FROM douplus_order_stats 
            ORDER BY stat_time DESC
        """))
        
        stat_times = [row[0] for row in result.fetchall()]
        logger.info(f"发现{len(stat_times)}个不同的时间窗口需要聚合")
        
        # 3. 逐个窗口聚合
        task = VideoAggTask()
        success_count = 0
        fail_count = 0
        
        for stat_time in stat_times:
            try:
                task.aggregate_video_stats(stat_time)
                success_count += 1
            except Exception as e:
                logger.error(f"聚合窗口{stat_time}失败: {e}")
                fail_count += 1
        
        logger.info(f"视频预聚合表重建完成: 成功{success_count}个窗口, 失败{fail_count}个窗口")
        
    except Exception as e:
        logger.error(f"重建视频预聚合表失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
