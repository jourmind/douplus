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
    
    修复逻辑：按订单创建时间筛选，从原始订单表和效果表汇总
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 构建时间筛选条件
        time_filter = ""
        params = {'account_id': account_id, 'user_id': user_id}
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 从原始订单表和效果表查询（按订单创建时间筛选）
        # MySQL 5.7兼容：使用子查询获取每个订单的最新效果数据
        stats_sql = text(f"""
            SELECT 
                SUM(COALESCE(s.stat_cost, 0)) as total_cost,
                SUM(COALESCE(s.total_play, 0)) as total_play,
                SUM(COALESCE(s.custom_like, 0)) as total_like,
                SUM(COALESCE(s.dy_comment, 0)) as total_comment,
                SUM(COALESCE(s.dy_share, 0)) as total_share,
                SUM(COALESCE(s.dy_follow, 0)) as total_follow,
                SUM(COALESCE(s.dp_target_convert_cnt, 0)) as total_convert,
                COUNT(DISTINCT o.item_id) as video_count,
                COUNT(DISTINCT o.id) as order_count
            FROM douplus_order o
            LEFT JOIN douplus_order_stats s ON o.order_id = s.order_id
            LEFT JOIN (
                SELECT order_id, MAX(stat_time) as max_time
                FROM douplus_order_stats
                GROUP BY order_id
            ) s_max ON s.order_id = s_max.order_id AND s.stat_time = s_max.max_time
            WHERE o.account_id = :account_id 
              AND o.user_id = :user_id 
              AND o.deleted = 0
              AND (s.stat_time IS NULL OR s_max.max_time IS NOT NULL)
              {time_filter}
        """)
        
        result = db.execute(stats_sql, params).fetchone()
        
        if result and result[0] is not None:
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
    获取用户所有账号的汇总统计（支持时间维度 + 账号筛选）
    
    参数：
    - period: today/7d/30d/all（默认all）
    - accountId: 筛选指定抖音账号的数据（可选）
    
    返回：所有账号（或指定账号）加总的统计数据
    
    修复：按订单创建时间筛选，从原始订单表汇总
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    account_id = request.args.get('accountId')  # 新增：账号筛选参数
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 构建筛选条件
        time_filter = ""
        account_filter = ""
        params = {'user_id': user_id}
        
        # 如果指定了accountId，则筛选该账号的数据
        if account_id:
            account_filter = "AND o.account_id = :account_id"
            params['account_id'] = int(account_id)
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 从原始订单表和效果表查询（按订单创建时间筛选）
        # MySQL 5.7兼容：使用子查询获取每个订单的最新效果数据
        stats_sql = text(f"""
            SELECT 
                SUM(COALESCE(s.stat_cost, 0)) as total_cost,
                SUM(COALESCE(s.total_play, 0)) as total_play,
                SUM(COALESCE(s.custom_like, 0)) as total_like,
                SUM(COALESCE(s.dy_comment, 0)) as total_comment,
                SUM(COALESCE(s.dy_share, 0)) as total_share,
                SUM(COALESCE(s.dy_follow, 0)) as total_follow,
                SUM(COALESCE(s.dp_target_convert_cnt, 0)) as total_convert,
                COUNT(DISTINCT o.item_id) as video_count,
                COUNT(DISTINCT o.id) as order_count
            FROM douplus_order o
            LEFT JOIN douplus_order_stats s ON o.order_id = s.order_id
            LEFT JOIN (
                SELECT order_id, MAX(stat_time) as max_time
                FROM douplus_order_stats
                GROUP BY order_id
            ) s_max ON s.order_id = s_max.order_id AND s.stat_time = s_max.max_time
            WHERE o.user_id = :user_id 
              AND o.deleted = 0
              AND (s.stat_time IS NULL OR s_max.max_time IS NOT NULL)
              {account_filter}
              {time_filter}
        """)
        
        result = db.execute(stats_sql, params).fetchone()
        
        if result and result[0] is not None:
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
