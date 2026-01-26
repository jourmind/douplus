"""
统计层API - 数据聚合与统计计算

职责：
1. 账号维度统计（单账号、全部账号汇总）
2. 视频维度统计（单账号、全部账号）
3. 支持多时间周期（today/7d/30d/all）

架构原则：
- 从预聚合表douplus_video_stats_agg查询
- 不做复杂JOIN，性能优先
- 统一时间维度处理逻辑
"""

import logging
from datetime import datetime, timedelta
from flask import request
from sqlalchemy import text
from app.api import stats_bp
from app.api.common import require_auth, success_response, error_response, paginated_response
from app.models import SessionLocal

logger = logging.getLogger(__name__)


def parse_time_period(period='all'):
    """
    解析时间周期参数，返回start_time
    
    Args:
        period: today/7d/30d/all
    
    Returns:
        datetime or None
    """
    now = datetime.now()
    if period == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == '7d':
        return now - timedelta(days=7)
    elif period == '30d':
        return now - timedelta(days=30)
    else:  # all
        return None


@stats_bp.route('/task/stats/<int:account_id>', methods=['GET'])
@require_auth
def get_account_stats(account_id):
    """
    获取指定账号的统计数据（支持时间维度）
    
    参数：
    - period: today/7d/30d/all（默认all）
    
    返回：总消耗、总播放、总点赞等统计数据
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 构建查询条件
        where_conditions = ["account_id = :account_id", "user_id = :user_id"]
        params = {'account_id': account_id, 'user_id': user_id}
        
        if start_time:
            where_conditions.append("stat_time >= :start_time")
            params['start_time'] = start_time
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询最新的stat_time
        latest_time_sql = text(f"""
            SELECT MAX(stat_time) 
            FROM douplus_video_stats_agg
            WHERE {where_clause}
        """)
        
        latest_time_result = db.execute(latest_time_sql, params).fetchone()
        latest_time = latest_time_result[0] if latest_time_result and latest_time_result[0] else None
        
        if not latest_time:
            return success_response({
                'cost': 0, 'playCount': 0, 'likeCount': 0, 'commentCount': 0,
                'shareCount': 0, 'fansCount': 0, 'convertCount': 0,
                'videoCount': 0, 'orderCount': 0
            })
        
        # 从预聚合表查询该账号的统计
        stats_sql = text(f"""
            SELECT 
                SUM(total_cost), SUM(total_play), SUM(total_like), SUM(total_comment),
                SUM(total_share), SUM(total_follow), SUM(total_convert),
                COUNT(DISTINCT item_id), SUM(order_count)
            FROM douplus_video_stats_agg
            WHERE {where_clause} AND stat_time = :stat_time
        """)
        
        params['stat_time'] = latest_time
        result = db.execute(stats_sql, params).fetchone()
        
        if result:
            return success_response({
                'cost': float(result[0]) if result[0] else 0,
                'playCount': int(result[1]) if result[1] else 0,
                'likeCount': int(result[2]) if result[2] else 0,
                'commentCount': int(result[3]) if result[3] else 0,
                'shareCount': int(result[4]) if result[4] else 0,
                'fansCount': int(result[5]) if result[5] else 0,
                'convertCount': int(result[6]) if result[6] else 0,
                'videoCount': int(result[7]) if result[7] else 0,
                'orderCount': int(result[8]) if result[8] else 0,
            })
        else:
            return success_response({
                'cost': 0, 'playCount': 0, 'likeCount': 0, 'commentCount': 0,
                'shareCount': 0, 'fansCount': 0, 'convertCount': 0,
                'videoCount': 0, 'orderCount': 0
            })
            
    except Exception as e:
        logger.error(f"查询账号统计失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@stats_bp.route('/task/stats', methods=['GET'])
@require_auth
def get_all_accounts_stats():
    """
    获取用户所有账号的汇总统计（支持时间维度）
    
    参数：
    - period: today/7d/30d/all（默认all）
    
    返回：所有账号加总的统计数据
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 查询最新的stat_time
        params = {'user_id': user_id}
        time_filter = "AND stat_time >= :start_time" if start_time else ""
        if start_time:
            params['start_time'] = start_time
        
        latest_time_sql = text(f"""
            SELECT MAX(stat_time) 
            FROM douplus_video_stats_agg
            WHERE user_id = :user_id {time_filter}
        """)
        
        latest_time_result = db.execute(latest_time_sql, params).fetchone()
        latest_time = latest_time_result[0] if latest_time_result and latest_time_result[0] else None
        
        if not latest_time:
            return success_response({
                'cost': 0, 'playCount': 0, 'likeCount': 0, 'commentCount': 0,
                'shareCount': 0, 'fansCount': 0, 'convertCount': 0,
                'videoCount': 0, 'orderCount': 0
            })
        
        # 从预聚合表查询用户所有账号的统计（汇总）
        stats_sql = text("""
            SELECT 
                SUM(total_cost), SUM(total_play), SUM(total_like), SUM(total_comment),
                SUM(total_share), SUM(total_follow), SUM(total_convert),
                COUNT(DISTINCT item_id), SUM(order_count)
            FROM douplus_video_stats_agg
            WHERE user_id = :user_id AND stat_time = :stat_time
        """)
        
        result = db.execute(stats_sql, {
            'user_id': user_id,
            'stat_time': latest_time
        }).fetchone()
        
        if result:
            return success_response({
                'cost': float(result[0]) if result[0] else 0,
                'playCount': int(result[1]) if result[1] else 0,
                'likeCount': int(result[2]) if result[2] else 0,
                'commentCount': int(result[3]) if result[3] else 0,
                'shareCount': int(result[4]) if result[4] else 0,
                'fansCount': int(result[5]) if result[5] else 0,
                'convertCount': int(result[6]) if result[6] else 0,
                'videoCount': int(result[7]) if result[7] else 0,
                'orderCount': int(result[8]) if result[8] else 0,
            })
        else:
            return success_response({
                'cost': 0, 'playCount': 0, 'likeCount': 0, 'commentCount': 0,
                'shareCount': 0, 'fansCount': 0, 'convertCount': 0,
                'videoCount': 0, 'orderCount': 0
            })
            
    except Exception as e:
        logger.error(f"查询用户统计失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()
