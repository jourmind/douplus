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
        # 首先验证账号是否存在且未解绑
        account_check_sql = text("""
            SELECT id FROM douyin_account 
            WHERE id = :account_id AND user_id = :user_id AND deleted = 0
        """)
        account_exists = db.execute(account_check_sql, {
            'account_id': account_id,
            'user_id': user_id
        }).fetchone()
        
        if not account_exists:
            # 账号已解绑，返回空数据
            return success_response({
                'cost': 0, 'playCount': 0, 'likeCount': 0, 'commentCount': 0,
                'shareCount': 0, 'fansCount': 0, 'convertCount': 0,
                'videoCount': 0, 'orderCount': 0
            })
        
        # 构建时间筛选条件
        time_filter = ""
        params = {'account_id': account_id, 'user_id': user_id}
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 从原始订单表和效果表查询（按订单创建时间筛选）
        # 修复：只JOIN每个订单的最新效果数据（避免重复）
        # 注意：使用COALESCE包裹SUM，确保无数据时返回0而不是NULL
        stats_sql = text(f"""
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
            WHERE o.account_id = :account_id 
              AND o.user_id = :user_id 
              AND o.deleted = 0
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
        
        # 从原始订单表和效果表查询（按订单创建时间筛选，过滤已解绑账号）
        # 修复：只JOIN每个订单的最新效果数据（避免重复）
        # 注意：使用COALESCE包裹SUM，确保无数据时返回0而不是NULL
        stats_sql = text(f"""
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


@stats_bp.route('/stats/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    """
    获取Dashboard统计数据（前端兼容接口）
    
    返回：用户全部统计数据
    """
    # 复用全部统计接口
    return get_user_all_stats()


@stats_bp.route('/video/rankings', methods=['GET'])
@require_auth
def get_video_rankings():
    """
    获取视频排行榜（前端兼容接口）
    
    返回：视频汇总数据
    """
    user_id = request.user_id
    
    # 获取分页参数
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    # 复用视频汇总接口逻辑
    # 这里返回空列表，待后续实现
    return paginated_response([], 0, page_num, page_size)


@stats_bp.route('/stats/refresh/<int:account_id>', methods=['POST'])
@require_auth
def refresh_account_stats(account_id):
    """
    刷新指定账号的效果数据
    
    手动触发单个账号的效果数据同步任务
    适用于用户在投放期间需要实时查看最新数据
    
    Args:
        account_id: 抖音账号ID
    
    Returns:
        同步的订单数量
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 验证账号归属
        account_check_sql = text("""
            SELECT id FROM douyin_account 
            WHERE id = :account_id AND user_id = :user_id AND deleted = 0
        """)
        account_exists = db.execute(account_check_sql, {
            'account_id': account_id,
            'user_id': user_id
        }).fetchone()
        
        if not account_exists:
            return error_response('账号不存在或已解绑', 404)
        
        # 调用同步任务
        from app.tasks.stats_sync import sync_single_account_stats
        
        try:
            sync_single_account_stats(account_id)
            
            # 查询该账号有多少订单有效果数据
            count_sql = text("""
                SELECT COUNT(*) 
                FROM douplus_order_stats s
                INNER JOIN douplus_order o ON s.order_id = o.order_id
                WHERE o.account_id = :account_id
            """)
            count = db.execute(count_sql, {'account_id': account_id}).scalar()
            
            return success_response({
                'count': count or 0,
                'message': f'成功刷新 {count or 0} 个订单的效果数据'
            })
            
        except Exception as e:
            logger.error(f"同步效果数据失败: account_id={account_id}, error={e}")
            return error_response(f'同步失败: {str(e)}')
            
    except Exception as e:
        logger.error(f"刷新效果数据失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()

