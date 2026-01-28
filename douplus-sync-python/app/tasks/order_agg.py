"""
订单维度预聚合任务

职责：
1. 从douplus_order_stats明细表聚合数据到douplus_order_agg
2. 计算百播放量、转化成本等指标
3. 避免查询时多层JOIN，提升性能
"""

import logging
from sqlalchemy import text
from app.models import get_db
from datetime import datetime

logger = logging.getLogger(__name__)


def aggregate_order_stats():
    """
    聚合所有订单的效果数据到预聚合表
    
    执行频率：效果数据同步后立即执行
    """
    db = get_db()
    try:
        # 使用INSERT ... ON DUPLICATE KEY UPDATE聚合数据
        sql = text("""
            INSERT INTO douplus_order_agg (
                order_id, item_id, account_id,
                total_cost, total_play, total_like, total_comment, total_share, 
                total_follow, total_convert, play_duration_5s,
                play_per_100_cost, avg_convert_cost, share_rate, like_rate, follow_rate,
                stat_time
            )
            SELECT 
                s.order_id,
                s.item_id,
                o.account_id,
                
                -- 原始指标聚合
                SUM(s.stat_cost) as total_cost,
                SUM(s.total_play) as total_play,
                SUM(s.custom_like) as total_like,
                SUM(s.dy_comment) as total_comment,
                SUM(s.dy_share) as total_share,
                SUM(s.dy_follow) as total_follow,
                SUM(s.dp_target_convert_cnt) as total_convert,
                AVG(s.play_duration_5s_rank) as play_duration_5s,
                
                -- 预聚合计算指标
                CASE 
                    WHEN SUM(s.stat_cost) > 0 
                    THEN SUM(s.total_play) / SUM(s.stat_cost) * 100 
                    ELSE 0 
                END as play_per_100_cost,
                
                CASE 
                    WHEN SUM(s.dp_target_convert_cnt) > 0 
                    THEN SUM(s.stat_cost) / SUM(s.dp_target_convert_cnt)
                    ELSE NULL 
                END as avg_convert_cost,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.dy_share) / SUM(s.total_play) * 100 
                    ELSE 0 
                END as share_rate,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.custom_like) / SUM(s.total_play)
                    ELSE 0 
                END as like_rate,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.dy_share) / SUM(s.total_play)
                    ELSE 0 
                END as follow_rate,
                
                MAX(s.stat_time) as stat_time
                
            FROM douplus_order_stats s
            INNER JOIN douplus_order o ON s.order_id = o.order_id
            GROUP BY s.order_id, s.item_id, o.account_id
            
            ON DUPLICATE KEY UPDATE
                account_id = VALUES(account_id),
                total_cost = VALUES(total_cost),
                total_play = VALUES(total_play),
                total_like = VALUES(total_like),
                total_comment = VALUES(total_comment),
                total_share = VALUES(total_share),
                total_follow = VALUES(total_follow),
                total_convert = VALUES(total_convert),
                play_duration_5s = VALUES(play_duration_5s),
                play_per_100_cost = VALUES(play_per_100_cost),
                avg_convert_cost = VALUES(avg_convert_cost),
                share_rate = VALUES(share_rate),
                like_rate = VALUES(like_rate),
                follow_rate = VALUES(follow_rate),
                stat_time = VALUES(stat_time),
                update_time = CURRENT_TIMESTAMP
        """)
        
        result = db.execute(sql)
        db.commit()
        
        affected_rows = result.rowcount
        logger.info(f"订单预聚合完成: 更新{affected_rows}个订单")
        return affected_rows
        
    except Exception as e:
        logger.error(f"订单预聚合失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def aggregate_single_account_orders(account_id: int):
    """
    聚合单个账号的订单效果数据
    
    Args:
        account_id: 账号ID
        
    用途：效果数据刷新后立即更新该账号的预聚合数据
    """
    db = get_db()
    try:
        sql = text("""
            INSERT INTO douplus_order_agg (
                order_id, item_id, account_id,
                total_cost, total_play, total_like, total_comment, total_share, 
                total_follow, total_convert, play_duration_5s,
                play_per_100_cost, avg_convert_cost, share_rate, like_rate, follow_rate,
                stat_time
            )
            SELECT 
                s.order_id,
                s.item_id,
                o.account_id,
                
                SUM(s.stat_cost) as total_cost,
                SUM(s.total_play) as total_play,
                SUM(s.custom_like) as total_like,
                SUM(s.dy_comment) as total_comment,
                SUM(s.dy_share) as total_share,
                SUM(s.dy_follow) as total_follow,
                SUM(s.dp_target_convert_cnt) as total_convert,
                AVG(s.play_duration_5s_rank) as play_duration_5s,
                
                CASE 
                    WHEN SUM(s.stat_cost) > 0 
                    THEN SUM(s.total_play) / SUM(s.stat_cost) * 100 
                    ELSE 0 
                END as play_per_100_cost,
                
                CASE 
                    WHEN SUM(s.dp_target_convert_cnt) > 0 
                    THEN SUM(s.stat_cost) / SUM(s.dp_target_convert_cnt)
                    ELSE NULL 
                END as avg_convert_cost,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.dy_share) / SUM(s.total_play) * 100 
                    ELSE 0 
                END as share_rate,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.custom_like) / SUM(s.total_play)
                    ELSE 0 
                END as like_rate,
                
                CASE 
                    WHEN SUM(s.total_play) > 0 
                    THEN SUM(s.dy_share) / SUM(s.total_play)
                    ELSE 0 
                END as follow_rate,
                
                MAX(s.stat_time) as stat_time
                
            FROM douplus_order_stats s
            INNER JOIN douplus_order o ON s.order_id = o.order_id
            WHERE o.account_id = :account_id
            GROUP BY s.order_id, s.item_id, o.account_id
            
            ON DUPLICATE KEY UPDATE
                account_id = VALUES(account_id),
                total_cost = VALUES(total_cost),
                total_play = VALUES(total_play),
                total_like = VALUES(total_like),
                total_comment = VALUES(total_comment),
                total_share = VALUES(total_share),
                total_follow = VALUES(total_follow),
                total_convert = VALUES(total_convert),
                play_duration_5s = VALUES(play_duration_5s),
                play_per_100_cost = VALUES(play_per_100_cost),
                avg_convert_cost = VALUES(avg_convert_cost),
                share_rate = VALUES(share_rate),
                like_rate = VALUES(like_rate),
                follow_rate = VALUES(follow_rate),
                stat_time = VALUES(stat_time),
                update_time = CURRENT_TIMESTAMP
        """)
        
        result = db.execute(sql, {'account_id': account_id})
        db.commit()
        
        affected_rows = result.rowcount
        logger.info(f"账号{account_id}订单预聚合完成: 更新{affected_rows}个订单")
        return affected_rows
        
    except Exception as e:
        logger.error(f"账号{account_id}订单预聚合失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    # 测试：聚合所有订单数据
    logging.basicConfig(level=logging.INFO)
    affected = aggregate_order_stats()
    print(f"聚合完成: {affected}个订单")
