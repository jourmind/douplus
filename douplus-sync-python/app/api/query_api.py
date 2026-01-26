"""
查询层API - 前端数据查询

职责：
1. 订单列表查询（分页、筛选、排序）
2. 视频维度统计查询
3. 数据展示相关接口

架构原则：
- 从预聚合表查询，无JOIN
- 支持分页、排序、筛选
- 响应时间<200ms
"""

import logging
from datetime import datetime, timedelta
from flask import request
from sqlalchemy import text
from app.api import query_bp
from app.api.common import require_auth, success_response, error_response, paginated_response
from app.models import SessionLocal

logger = logging.getLogger(__name__)


def parse_time_period(period='all'):
    """解析时间周期参数"""
    now = datetime.now()
    if period == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == '7d':
        return now - timedelta(days=7)
    elif period == '30d':
        return now - timedelta(days=30)
    else:
        return None


@query_bp.route('/task/page', methods=['GET'])
@require_auth
def get_task_page():
    """
    分页查询投放记录
    
    参数：
    - pageNum: 页码
    - pageSize: 每页数量
    - status: 状态筛选
    - accountId: 账号筛选
    - keyword: 视频标题关键词搜索
    - startDate: 开始日期（YYYY-MM-DD）
    - endDate: 结束日期（YYYY-MM-DD）
    - sortField: 排序字段
    - sortOrder: 排序方向
    """
    user_id = request.user_id
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))
    status = request.args.get('status')
    account_id = request.args.get('accountId')
    keyword = request.args.get('keyword')      # 新增：关键词搜索
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    sort_field = request.args.get('sortField', 'createTime')
    sort_order = request.args.get('sortOrder', 'desc')
    
    if page_size == -1:
        page_size = 10000
    
    db = SessionLocal()
    try:
        # 构建查询条件
        where_conditions = ["o.user_id = :user_id", "o.deleted = 0"]
        params = {
            'user_id': user_id,
            'limit': page_size,
            'offset': (page_num - 1) * page_size
        }
        
        if status:
            where_conditions.append("o.status = :status")
            params['status'] = status
        
        if account_id:
            where_conditions.append("o.account_id = :account_id")
            params['account_id'] = int(account_id)
        
        # 新增：视频标题关键词搜索
        if keyword:
            where_conditions.append("o.aweme_title LIKE :keyword")
            params['keyword'] = f'%{keyword}%'
        
        # 时间范围筛选
        if start_date:
            where_conditions.append("DATE(o.order_create_time) >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            where_conditions.append("DATE(o.order_create_time) <= :end_date")
            params['end_date'] = end_date
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM douplus_order o WHERE {where_clause}"
        total = db.execute(text(count_sql), params).fetchone()[0]
        
        # 查询订单数据
        order_mapping = {
            'createTime': 'create_time',
            'budget': 'budget',
            'scheduledTime': 'order_create_time'
        }
        order_column = order_mapping.get(sort_field, 'create_time')
        order_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        data_sql = f"""
            SELECT 
                o.id, o.user_id, o.account_id, o.item_id, o.order_id,
                o.status, o.budget, o.duration, o.target_type,
                o.aweme_title, o.aweme_cover, o.aweme_nick, o.aweme_avatar,
                o.order_create_time, o.order_start_time, o.order_end_time,
                o.create_time, o.update_time
            FROM douplus_order o
            WHERE {where_clause}
            ORDER BY o.{order_column} {order_direction}
            LIMIT :limit OFFSET :offset
        """
        
        results = db.execute(text(data_sql), params).fetchall()
        
        # 获取效果数据（从订单效果明细表，按order_id维度）
        order_ids = [row[4] for row in results if row[4]]  # order_id字段
        order_stats_map = {}
        
        if order_ids:
            # 查询每个订单的最新效果数据（优化：使用JOIN替代子查询）
            stats_sql = text("""
                SELECT 
                    s.order_id, 
                    s.stat_cost, 
                    s.total_play, 
                    s.custom_like, 
                    s.dy_comment, 
                    s.dy_share, 
                    s.dy_follow, 
                    s.dp_target_convert_cnt,
                    s.custom_convert_cost,
                    s.play_duration_5s_rank
                FROM douplus_order_stats s
                INNER JOIN (
                    SELECT order_id, MAX(stat_time) as max_time
                    FROM douplus_order_stats
                    WHERE order_id IN :order_ids
                    GROUP BY order_id
                ) latest ON s.order_id = latest.order_id AND s.stat_time = latest.max_time
            """)
            
            stats_results = db.execute(stats_sql, {
                'order_ids': tuple(order_ids)
            }).fetchall()
            
            for row in stats_results:
                order_stats_map[row[0]] = {
                    'actualCost': float(row[1]) if row[1] else 0,
                    'playCount': int(row[2]) if row[2] else 0,
                    'likeCount': int(row[3]) if row[3] else 0,
                    'commentCount': int(row[4]) if row[4] else 0,
                    'shareCount': int(row[5]) if row[5] else 0,
                    'followCount': int(row[6]) if row[6] else 0,
                    'dpTargetConvertCnt': int(row[7]) if row[7] else 0,
                    'avgConvertCost': float(row[8]) if row[8] else 0,  # 订单维度的转化成本
                    'avg5sRate': float(row[9]) if row[9] else 0,  # 订单维度的5S完播率
                }
        
        # 组装返回数据
        records = []
        for row in results:
            order_id = row[4]  # order_id字段
            stats = order_stats_map.get(order_id, {})
            
            # 计算结束时间：投放开始时间 + 投放时长
            order_end_time = None
            order_create_time = row[13]  # order_create_time
            duration = row[7]  # duration (小时)
            if order_create_time and duration:
                from datetime import timedelta
                if isinstance(order_create_time, str):
                    order_create_time = datetime.fromisoformat(order_create_time)
                order_end_time = order_create_time + timedelta(hours=duration)
            
            record = {
                'id': row[0],
                'userId': row[1],
                'accountId': row[2],
                'itemId': row[3],
                'orderId': order_id,
                'status': row[5],
                'budget': float(row[6]) if row[6] else 0,
                'duration': duration,
                'targetType': row[8],
                'videoTitle': row[9],
                'videoCoverUrl': row[10],
                'accountNickname': row[11],
                'accountAvatar': row[12],
                'orderCreateTime': row[13].isoformat() if row[13] else None,
                'orderStartTime': row[14].isoformat() if row[14] else None,
                'orderEndTime': order_end_time.isoformat() if order_end_time else None,  # 计算的结束时间
                'createTime': row[16].isoformat() if row[16] else None,
                'updateTime': row[17].isoformat() if row[17] else None,
                **stats
            }
            records.append(record)
        
        return paginated_response(records, total, page_num, page_size)
        
    except Exception as e:
        logger.error(f"查询订单列表失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return error_response(str(e))
    finally:
        db.close()


@query_bp.route('/video/stats/<int:account_id>', methods=['GET'])
@require_auth
def get_video_stats_by_account(account_id):
    """
    获取指定账号的视频维度统计列表
    
    参数：
    - period: 时间维度
    - sortBy: 排序字段
    - sortOrder: 排序方向
    - pageNum/pageSize: 分页参数
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    sort_by = request.args.get('sortBy', 'cost')
    sort_order = request.args.get('sortOrder', 'desc')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 时间筛选条件（基于订单创建时间）
        time_filter = ""
        params = {'account_id': account_id, 'user_id': user_id, 'limit': page_size, 'offset': (page_num - 1) * page_size}
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 排序字段映射
        sort_mapping = {'cost': 'total_cost', 'playCount': 'total_play', 'likeCount': 'total_like', 
                       'commentCount': 'total_comment', 'shareCount': 'total_share', 'convertCount': 'total_convert'}
        sort_column = sort_mapping.get(sort_by, 'total_cost')
        sort_dir = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        # 修复：按订单创建时间筛选，从订单表聚合视频维度数据
        # MySQL 5.7兼容：使用子查询获取每个订单的最新效果数据
        video_sql = text(f"""
            SELECT 
                o.item_id,
                MAX(o.aweme_title) as title,
                MAX(o.aweme_cover) as cover,
                COUNT(DISTINCT o.id) as order_count,
                SUM(o.budget) as total_budget,
                SUM(COALESCE(s.stat_cost, 0)) as total_cost,
                SUM(COALESCE(s.total_play, 0)) as total_play,
                SUM(COALESCE(s.custom_like, 0)) as total_like,
                SUM(COALESCE(s.dy_comment, 0)) as total_comment,
                SUM(COALESCE(s.dy_share, 0)) as total_share,
                SUM(COALESCE(s.dy_follow, 0)) as total_follow,
                SUM(COALESCE(s.dp_target_convert_cnt, 0)) as total_convert
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
            GROUP BY o.item_id
            ORDER BY {sort_column} {sort_dir}
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(video_sql, params).fetchall()
        
        # 查询总数
        count_sql = text(f"""
            SELECT COUNT(DISTINCT o.item_id) 
            FROM douplus_order o 
            WHERE o.account_id = :account_id 
              AND o.user_id = :user_id 
              AND o.deleted = 0
              {time_filter}
        """)
        total = db.execute(count_sql, params).fetchone()[0]
        
        records = [{'itemId': r[0], 'title': r[1] or '未知视频', 'cover': r[2] or '', 'orderCount': r[3] or 0,
                   'totalBudget': float(r[4]) if r[4] else 0, 'totalCost': float(r[5]) if r[5] else 0,
                   'totalPlay': int(r[6]) if r[6] else 0, 'totalLike': int(r[7]) if r[7] else 0,
                   'totalComment': int(r[8]) if r[8] else 0, 'totalShare': int(r[9]) if r[9] else 0,
                   'totalFollow': int(r[10]) if r[10] else 0, 'totalConvert': int(r[11]) if r[11] else 0} for r in results]
        
        return paginated_response(records, total, page_num, page_size)
        
    except Exception as e:
        logger.error(f"查询视频统计失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return error_response(str(e))
    finally:
        db.close()


@query_bp.route('/video/stats/all', methods=['GET'])
@require_auth
def get_all_video_stats():
    """
    获取所有账号的视频维度统计列表（支持时间维度 + 账号筛选）
    
    参数：
    - period: 时间周期
    - accountId: 筛选指定抖音账号的数据（可选）
    - sortBy/sortOrder/pageNum/pageSize: 排序和分页
    
    修复：按订单创建时间筛选，从原始订单表聚合
    """
    user_id = request.user_id
    period = request.args.get('period', 'all')
    account_id = request.args.get('accountId')  # 新增：账号筛选参数
    sort_by = request.args.get('sortBy', 'cost')
    sort_order = request.args.get('sortOrder', 'desc')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    start_time = parse_time_period(period)
    
    db = SessionLocal()
    try:
        # 筛选条件
        time_filter = ""
        account_filter = ""
        params = {'user_id': user_id, 'limit': page_size, 'offset': (page_num - 1) * page_size}
        
        # 如果指定了accountId，则筛选该账号的数据
        if account_id:
            account_filter = "AND o.account_id = :account_id"
            params['account_id'] = int(account_id)
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 排序字段映射
        sort_mapping = {'cost': 'total_cost', 'playCount': 'total_play', 'likeCount': 'total_like', 
                       'shareCount': 'total_share', 'convertCount': 'total_convert'}
        sort_column = sort_mapping.get(sort_by, 'total_cost')
        sort_dir = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        # 从订单表聚合视频维度数据
        video_sql = text(f"""
            SELECT 
                o.item_id,
                MAX(o.aweme_title) as title,
                MAX(o.aweme_cover) as cover,
                COUNT(DISTINCT o.id) as order_count,
                SUM(COALESCE(s.stat_cost, 0)) as total_cost,
                SUM(COALESCE(s.total_play, 0)) as total_play,
                SUM(COALESCE(s.custom_like, 0)) as total_like,
                SUM(COALESCE(s.dy_comment, 0)) as total_comment,
                SUM(COALESCE(s.dy_share, 0)) as total_share
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
            GROUP BY o.item_id
            ORDER BY {sort_column} {sort_dir}
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(video_sql, params).fetchall()
        
        # 查询总数
        count_sql = text(f"""
            SELECT COUNT(DISTINCT o.item_id) 
            FROM douplus_order o 
            WHERE o.user_id = :user_id 
              AND o.deleted = 0
              {account_filter}
              {time_filter}
        """)
        total = db.execute(count_sql, params).fetchone()[0]
        
        records = [{'itemId': r[0], 'title': r[1] or '未知视频', 'cover': r[2] or '', 'orderCount': r[3] or 0,
                   'totalCost': float(r[4]) if r[4] else 0, 'totalPlay': int(r[5]) if r[5] else 0,
                   'totalLike': int(r[6]) if r[6] else 0, 'totalComment': int(r[7]) if r[7] else 0,
                   'totalShare': int(r[8]) if r[8] else 0} for r in results]
        
        return paginated_response(records, total, page_num, page_size)
        
    except Exception as e:
        logger.error(f"查询视频统计失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@query_bp.route('/task/<int:task_id>', methods=['GET'])
@require_auth
def get_task_detail(task_id):
    """
    获取订单详情
    
    参数：
    - task_id: 订单ID
    
    返回：订单基础信息 + 最新效果数据
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 查询订单基础信息
        order_sql = text("""
            SELECT 
                o.id, o.user_id, o.account_id, o.item_id, o.order_id,
                o.status, o.budget, o.duration, o.target_type,
                o.aweme_title, o.aweme_cover, o.aweme_nick, o.aweme_avatar,
                o.order_create_time, o.order_start_time, o.order_end_time,
                o.create_time, o.update_time
            FROM douplus_order o
            WHERE o.id = :task_id AND o.user_id = :user_id AND o.deleted = 0
        """)
        
        row = db.execute(order_sql, {
            'task_id': task_id,
            'user_id': user_id
        }).fetchone()
        
        if not row:
            return error_response('订单不存在', code=404)
        
        # 查询订单的最新效果数据（使用order_id维度）
        order_id = row[4]
        stats = {}
        
        if order_id:
            stats_sql = text("""
                SELECT 
                    s.stat_cost, 
                    s.total_play, 
                    s.custom_like, 
                    s.dy_comment, 
                    s.dy_share, 
                    s.dy_follow, 
                    s.dp_target_convert_cnt,
                    s.custom_convert_cost,
                    s.play_duration_5s_rank
                FROM douplus_order_stats s
                WHERE s.order_id = :order_id
                ORDER BY s.stat_time DESC
                LIMIT 1
            """)
            
            stats_row = db.execute(stats_sql, {
                'order_id': order_id
            }).fetchone()
            
            if stats_row:
                stats = {
                    'actualCost': float(stats_row[0]) if stats_row[0] else 0,
                    'playCount': int(stats_row[1]) if stats_row[1] else 0,
                    'likeCount': int(stats_row[2]) if stats_row[2] else 0,
                    'commentCount': int(stats_row[3]) if stats_row[3] else 0,
                    'shareCount': int(stats_row[4]) if stats_row[4] else 0,
                    'followCount': int(stats_row[5]) if stats_row[5] else 0,
                    'dpTargetConvertCnt': int(stats_row[6]) if stats_row[6] else 0,
                    'avgConvertCost': float(stats_row[7]) if stats_row[7] else 0,
                    'avg5sRate': float(stats_row[8]) if stats_row[8] else 0,
                }
        
        # 计算结束时间
        order_end_time = None
        order_create_time = row[13]
        duration = row[7]
        if order_create_time and duration:
            from datetime import timedelta
            if isinstance(order_create_time, str):
                order_create_time = datetime.fromisoformat(order_create_time)
            order_end_time = order_create_time + timedelta(hours=duration)
        
        # 组装返回数据
        task_detail = {
            'id': row[0],
            'userId': row[1],
            'accountId': row[2],
            'itemId': row[3],  # item_id
            'orderId': order_id,
            'status': row[5],
            'budget': float(row[6]) if row[6] else 0,
            'duration': duration,
            'targetType': row[8],
            'videoTitle': row[9],
            'videoCoverUrl': row[10],
            'accountNickname': row[11],
            'accountAvatar': row[12],
            'orderCreateTime': row[13].isoformat() if row[13] else None,
            'orderStartTime': row[14].isoformat() if row[14] else None,
            'orderEndTime': order_end_time.isoformat() if order_end_time else None,
            'createTime': row[16].isoformat() if row[16] else None,
            'updateTime': row[17].isoformat() if row[17] else None,
            **stats
        }
        
        return success_response(task_detail)
        
    except Exception as e:
        logger.error(f"查询订单详情失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()
