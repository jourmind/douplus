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
        # 构建查询条件（包含账号表JOIN，过滤已解绑账号）
        where_conditions = [
            "o.user_id = :user_id", 
            "o.deleted = 0",
            "a.deleted = 0"  # 新增：过滤已解绑的账号
        ]
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
        
        # 查询总数（JOIN账号表）
        count_sql = f"""
            SELECT COUNT(*) 
            FROM douplus_order o
            INNER JOIN douyin_account a ON o.account_id = a.id
            WHERE {where_clause}
        """
        total = db.execute(text(count_sql), params).fetchone()[0]
        
        # 判断是否需要JOIN效果表进行排序
        effect_sort_fields = ['playCount', 'actualCost', 'likeCount', 'shareCount', 'commentCount', 
                              'followCount', 'dpTargetConvertCnt', 'costPerPlay', 'shareRate']
        need_join_stats = sort_field in effect_sort_fields
        
        order_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        if need_join_stats:
            # 需要JOIN预聚合表进行排序（按视频维度）
            # 排序字段映射
            # 注意：前端'playCount'在SortCascader中实际指百播放量（播放量/消耗*100），而不是播放量
            
            # 转化成本排序：空值处理根据排序方向决定
            # DESC: 空值用NULL（自动排最后） 或者用负数
            # ASC: 空值用NULL（自动排最前） 或者用大数
            if sort_field == 'costPerPlay':
                if sort_order.lower() == 'desc':
                    # 降序：空值应该排最后，用负数或NULL
                    cost_per_play_expr = 'CASE WHEN v.total_convert > 0 THEN v.total_cost / v.total_convert ELSE NULL END'
                else:
                    # 升序：空值应该排最后，用大数
                    cost_per_play_expr = 'CASE WHEN v.total_convert > 0 THEN v.total_cost / v.total_convert ELSE 999999 END'
            else:
                cost_per_play_expr = 'CASE WHEN v.total_convert > 0 THEN v.total_cost / v.total_convert ELSE 0 END'
            
            stats_field_mapping = {
                'playCount': 'CASE WHEN v.total_cost > 0 THEN (v.total_play / v.total_cost * 100) ELSE 0 END',  # 百播放量
                'actualCost': 'v.total_cost',
                'likeCount': 'v.total_like',
                'shareCount': 'v.total_share',
                'commentCount': 'v.total_comment',
                'followCount': 'v.total_follow',
                'dpTargetConvertCnt': 'v.total_convert',
                'costPerPlay': cost_per_play_expr,  # 转化成本（动态处理空值）
                'shareRate': 'CASE WHEN v.total_play > 0 THEN (v.total_share / v.total_play * 100) ELSE 0 END'  # 百转发率
            }
            sort_column = stats_field_mapping.get(sort_field, 'v.total_cost')
            
            # LEFT JOIN预聚合表（取最新数据），INNER JOIN账号表（过滤已解绑）
            data_sql = f"""
                SELECT 
                    o.id, o.user_id, o.account_id, o.item_id, o.order_id,
                    o.status, o.budget, o.duration, o.target_type,
                    o.aweme_title, o.aweme_cover, o.aweme_nick, o.aweme_avatar,
                    o.order_create_time, o.order_start_time, o.order_end_time,
                    o.create_time, o.update_time
                FROM douplus_order o
                INNER JOIN douyin_account a ON o.account_id = a.id
                LEFT JOIN (
                    SELECT v1.item_id, v1.total_cost, v1.total_play, v1.total_like, 
                           v1.total_share, v1.total_comment, v1.total_follow, v1.total_convert
                    FROM douplus_video_stats_agg v1
                    INNER JOIN (
                        SELECT item_id, MAX(stat_time) as max_time
                        FROM douplus_video_stats_agg
                        GROUP BY item_id
                    ) v2 ON v1.item_id = v2.item_id AND v1.stat_time = v2.max_time
                ) v ON o.item_id = v.item_id
                WHERE {where_clause}
                ORDER BY {sort_column} {order_direction}
                LIMIT :limit OFFSET :offset
            """
        else:
            # 按订单表字段排序（如创建时间、预算等）
            order_mapping = {
                'createTime': 'o.create_time',
                'budget': 'o.budget',
                'scheduledTime': 'o.order_create_time'
            }
            order_column = order_mapping.get(sort_field, 'o.create_time')
            
            data_sql = f"""
                SELECT 
                    o.id, o.user_id, o.account_id, o.item_id, o.order_id,
                    o.status, o.budget, o.duration, o.target_type,
                    o.aweme_title, o.aweme_cover, o.aweme_nick, o.aweme_avatar,
                    o.order_create_time, o.order_start_time, o.order_end_time,
                    o.create_time, o.update_time
                FROM douplus_order o
                INNER JOIN douyin_account a ON o.account_id = a.id
                WHERE {where_clause}
                ORDER BY {order_column} {order_direction}
                LIMIT :limit OFFSET :offset
            """
        
        results = db.execute(text(data_sql), params).fetchall()
        
        # 获取效果数据（从视频预聚合表，按item_id维度）
        item_ids = [row[3] for row in results if row[3]]  # item_id字段
        video_stats_map = {}
        
        if item_ids:
            # 查询视频维度的最新效果数据（使用预聚合表）
            stats_sql = text("""
                SELECT 
                    v.item_id,
                    v.total_cost,
                    v.total_play,
                    v.total_like,
                    v.total_comment,
                    v.total_share,
                    v.total_follow,
                    v.total_convert,
                    v.avg_convert_cost,
                    v.avg_5s_rank
                FROM douplus_video_stats_agg v
                INNER JOIN (
                    SELECT item_id, MAX(stat_time) as max_time
                    FROM douplus_video_stats_agg
                    WHERE item_id IN :item_ids
                    GROUP BY item_id
                ) latest ON v.item_id = latest.item_id AND v.stat_time = latest.max_time
            """)
            
            stats_results = db.execute(stats_sql, {
                'item_ids': tuple(item_ids)
            }).fetchall()
            
            for row in stats_results:
                video_stats_map[row[0]] = {
                    'actualCost': float(row[1]) if row[1] else 0,
                    'playCount': int(row[2]) if row[2] else 0,
                    'likeCount': int(row[3]) if row[3] else 0,
                    'commentCount': int(row[4]) if row[4] else 0,
                    'shareCount': int(row[5]) if row[5] else 0,
                    'followCount': int(row[6]) if row[6] else 0,
                    'dpTargetConvertCnt': int(row[7]) if row[7] else 0,
                    'customConvertCost': float(row[8]) if row[8] else 0,
                    'avg5sRate': float(row[9]) if row[9] else 0,
                }
        
        # 组装返回数据
        records = []
        for row in results:
            order_id = row[4]  # order_id字段
            item_id = row[3]  # item_id字段
            stats = video_stats_map.get(item_id, {})  # 使用视频维度的效果数据
            
            # 计算结束时间：创建时间 + 时长（考虑续费）
            order_end_time = None
            order_create_time = row[13]  # order_create_time
            duration = row[7]  # duration (小时，包含续费后的总时长)
            if order_create_time and duration:
                from datetime import timedelta
                if isinstance(order_create_time, str):
                    order_create_time = datetime.fromisoformat(order_create_time)
                order_end_time = order_create_time + timedelta(hours=duration)
            
            record = {
                'id': row[0],
                'userId': row[1],
                'accountId': row[2],
                'itemId': item_id,
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
            return error_response('账号不存在或已解绑', code=404)
        
        # 时间筛选条件（基于订单创建时间，与统计卡片保持一致）
        time_filter = ""
        params = {'account_id': account_id, 'user_id': user_id, 'limit': page_size, 'offset': (page_num - 1) * page_size}
        
        if start_time:
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 排序字段映射（包含计算字段）
        # 注意：前端'playCount'实际指的是百播放量，而不是播放量
        sort_mapping = {
            'cost': 'total_cost', 
            'playCount': 'play_per_100_cost',      # 前端playCount = 百播放量
            'likeCount': 'total_like', 
            'commentCount': 'total_comment', 
            'shareCount': 'total_share', 
            'convertCount': 'total_convert',
            'playPer100Cost': 'play_per_100_cost',  # 百播放量（备用）
            'shareRate': 'share_per_100_play',      # 百转发率
            'convertCost': 'avg_convert_cost',      # 转化成本
            'costPerPlay': 'avg_convert_cost'       # 前端costPerPlay = 转化成本
        }
        sort_column = sort_mapping.get(sort_by, 'total_cost')
        sort_dir = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        # 方案A：从预聚合表查询（5分钟粒度），按天聚合
        # 优势：查询解耦，无JOIN，性能优异
        video_sql = text(f"""
            SELECT 
                v.item_id,
                MAX(o.aweme_title) as title,
                MAX(o.aweme_cover) as cover,
                COUNT(DISTINCT o.order_id) as order_count,
                COALESCE(SUM(o.budget), 0) as total_budget,
                COALESCE(SUM(v.total_cost), 0) as total_cost,
                COALESCE(SUM(v.total_play), 0) as total_play,
                COALESCE(SUM(v.total_like), 0) as total_like,
                COALESCE(SUM(v.total_comment), 0) as total_comment,
                COALESCE(SUM(v.total_share), 0) as total_share,
                COALESCE(SUM(v.total_follow), 0) as total_follow,
                COALESCE(SUM(v.total_convert), 0) as total_convert,
                CASE 
                    WHEN SUM(v.total_cost) > 0 
                    THEN SUM(v.total_play) / SUM(v.total_cost) * 100
                    ELSE 0 
                END as play_per_100_cost,
                CASE 
                    WHEN SUM(v.total_play) > 0 
                    THEN SUM(v.total_share) / SUM(v.total_play) * 100
                    ELSE 0 
                END as share_per_100_play,
                CASE 
                    WHEN SUM(v.total_convert) > 0 
                    THEN SUM(v.total_cost) / SUM(v.total_convert)
                    ELSE 0 
                END as avg_convert_cost
            FROM douplus_video_stats_agg v
            INNER JOIN douplus_order o ON v.item_id = o.item_id AND o.account_id = v.account_id
            WHERE v.account_id = :account_id 
              AND v.user_id = :user_id
              {time_filter}
            GROUP BY v.item_id
            ORDER BY {sort_column} {sort_dir}
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(video_sql, params).fetchall()
        
        # 查询总数（需要JOIN订单表才能按订单创建时间筛选）
        count_sql = text(f"""
            SELECT COUNT(DISTINCT v.item_id) 
            FROM douplus_video_stats_agg v
            INNER JOIN douplus_order o ON v.item_id = o.item_id AND o.account_id = v.account_id
            WHERE v.account_id = :account_id 
              AND v.user_id = :user_id
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
        # 筛选条件（包含账号过滤）
        time_filter = ""
        account_filter_order = ""  # 用于主查询（有订单表JOIN）
        account_filter_video = ""  # 用于COUNT查询（只有视频表）
        params = {'user_id': user_id, 'limit': page_size, 'offset': (page_num - 1) * page_size}
        
        # 如果指定了accountId，则筛选该账号的数据
        if account_id:
            account_filter_order = "AND o.account_id = :account_id"
            account_filter_video = "AND v.account_id = :account_id"
            params['account_id'] = int(account_id)
        
        if start_time:
            # 修复：使用订单创建时间筛选，与统计卡片保持一致
            time_filter = "AND o.order_create_time >= :start_time"
            params['start_time'] = start_time
        
        # 排序字段映射（包含计算字段）
        # 注意：这个API用于Dashboard视频排行榜，playCount指真实播放量
        sort_mapping = {
            'cost': 'total_cost', 
            'playCount': 'total_play',                  # Dashboard排行榜：按播放量排序
            'likeCount': 'total_like', 
            'shareCount': 'total_share', 
            'convertCount': 'total_convert',
            'playPer100Cost': 'play_per_100_cost',  # 百播放量
            'shareRate': 'share_per_100_play',      # 百转发率
            'convertCost': 'avg_convert_cost',      # 转化成本
            'costPerPlay': 'avg_convert_cost'       # 前端costPerPlay = 转化成本
        }
        sort_column = sort_mapping.get(sort_by, 'total_cost')
        sort_dir = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        # 使用预聚合表 + min_order_create_time精确筛选
        # 核心：预聚合表新增了min_order_create_time字段，记录视频最早订单创建时间
        # 优势：时间精度完全准确，与统计卡片完全一致
        video_sql = text(f"""
            SELECT 
                v.item_id,
                MAX(o.aweme_title) as title,
                MAX(o.aweme_cover) as cover,
                MAX(v.order_count) as order_count,
                COALESCE(SUM(v.total_cost), 0) as total_cost,
                COALESCE(SUM(v.total_play), 0) as total_play,
                COALESCE(SUM(v.total_like), 0) as total_like,
                COALESCE(SUM(v.total_comment), 0) as total_comment,
                COALESCE(SUM(v.total_share), 0) as total_share,
                COALESCE(SUM(v.total_follow), 0) as total_follow,
                CASE 
                    WHEN SUM(v.total_cost) > 0 
                    THEN SUM(v.total_play) / SUM(v.total_cost) * 100
                    ELSE 0 
                END as play_per_100_cost,
                CASE 
                    WHEN SUM(v.total_play) > 0 
                    THEN SUM(v.total_share) / SUM(v.total_play) * 100
                    ELSE 0 
                END as share_per_100_play,
                CASE 
                    WHEN SUM(v.total_convert) > 0 
                    THEN SUM(v.total_cost) / SUM(v.total_convert)
                    ELSE 0 
                END as avg_convert_cost
            FROM douplus_video_stats_agg v
            INNER JOIN douplus_order o ON v.item_id = o.item_id AND v.account_id = o.account_id
            WHERE v.user_id = :user_id
              {account_filter_video.replace('v.', 'v.')}
              {time_filter.replace('o.order_create_time', 'v.min_order_create_time')}
            GROUP BY v.item_id
            ORDER BY {sort_column} {sort_dir}
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(video_sql, params).fetchall()
        
        # 统计总数（使用相同的筛选逻辑）
        count_sql = text(f"""
            SELECT COUNT(DISTINCT v.item_id)
            FROM douplus_video_stats_agg v
            WHERE v.user_id = :user_id
              {account_filter_video}
              {time_filter.replace('o.order_create_time', 'v.min_order_create_time')}
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
        
        # 查询视频维度的最新效果数据（使用预聚合表）
        item_id = row[3]
        stats = {}
        
        if item_id:
            stats_sql = text("""
                SELECT 
                    v.total_cost,
                    v.total_play,
                    v.total_like,
                    v.total_comment,
                    v.total_share,
                    v.total_follow,
                    v.total_convert,
                    v.avg_convert_cost,
                    v.avg_5s_rank
                FROM douplus_video_stats_agg v
                WHERE v.item_id = :item_id
                ORDER BY v.stat_time DESC
                LIMIT 1
            """)
            
            stats_row = db.execute(stats_sql, {
                'item_id': item_id
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
        
        # 直接使用API返回的order_end_time
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
            'itemId': item_id,
            'orderId': row[4],  # order_id
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
        
        return success_response(task_detail)
        
    except Exception as e:
        logger.error(f"查询订单详情失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@query_bp.route('/video/titles', methods=['GET'])
@require_auth
def get_video_titles():
    """
    获取视频标题列表（用于筛选器下拉选择）
    
    参数：
    - accountId: 账号ID（可选）
    """
    user_id = request.user_id
    account_id = request.args.get('accountId')
    
    db = SessionLocal()
    try:
        # 构建查询条件
        where_conditions = ["o.user_id = :user_id", "o.deleted = 0", "o.aweme_title IS NOT NULL"]
        params = {'user_id': user_id}
        
        if account_id:
            where_conditions.append("o.account_id = :account_id")
            params['account_id'] = int(account_id)
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询不重复的视频标题
        sql = text(f"""
            SELECT DISTINCT o.aweme_title
            FROM douplus_order o
            WHERE {where_clause}
            ORDER BY o.aweme_title
            LIMIT 100
        """)
        
        results = db.execute(sql, params).fetchall()
        titles = [{'label': row[0], 'value': row[0]} for row in results]
        
        return success_response(titles)
        
    except Exception as e:
        logger.error(f"查询视频标题失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()
