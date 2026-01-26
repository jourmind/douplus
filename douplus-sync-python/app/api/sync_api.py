"""
同步层API - 订单采集与历史同步

职责：
1. 触发订单同步（全量/增量）
2. 查询同步状态
3. DOU+平台回调接收

架构原则：
- 只负责数据采集，不做统计计算
- 调用Celery任务异步执行
- 返回任务提交状态
"""

import logging
from flask import request
from sqlalchemy import text
from app.api import sync_bp
from app.api.common import require_auth, success_response, error_response
from app.models import SessionLocal

logger = logging.getLogger(__name__)

# 全局同步状态（简化版，生产环境应使用Redis）
sync_status = {}


@sync_bp.route('/task/sync-all', methods=['POST'])
@require_auth
def sync_all_orders():
    """
    同步所有账号的DOU+历史订单（全量同步）
    
    触发机制：用户点击"同步历史订单"按钮
    执行方式：异步Celery任务
    """
    user_id = request.user_id
    
    logger.info(f"收到全量同步请求，用户ID: {user_id}")
    
    # 检查是否正在同步
    if user_id in sync_status and sync_status[user_id].get('status') == 'syncing':
        return success_response(
            data=sync_status[user_id],
            message='正在同步中，请稍候...'
        )
    
    # 初始化同步状态
    sync_status[user_id] = {
        'status': 'syncing',
        'count': 0,
        'message': '正在初始化同步...'
    }
    
    # 获取该用户的所有账号
    db = SessionLocal()
    try:
        query_sql = text("""
            SELECT id, advertiser_id, nickname
            FROM douyin_account
            WHERE user_id = :user_id AND status = 1 AND deleted = 0
        """)
        
        accounts = db.execute(query_sql, {'user_id': user_id}).fetchall()
        
        if not accounts:
            sync_status[user_id] = {
                'status': 'error',
                'count': 0,
                'message': '没有可用的抖音账号'
            }
            return error_response('没有可用的抖音账号', code=400, data=sync_status[user_id])
        
        # 异步触发每个账号的全量同步任务
        from celery_app import app as celery_app
        for account in accounts:
            account_id = account[0]  # id
            celery_app.send_task(
                'app.tasks.order_sync.sync_single_account',
                args=[account_id, 'full']
            )
            logger.info(f"已提交账号{account_id}的全量同步任务到Celery队列")
        
        sync_status[user_id] = {
            'status': 'completed',
            'count': len(accounts),
            'message': f'已提交{len(accounts)}个账号的同步任务到后台队列，请稍后查看订单数据'
        }
        
        return success_response(
            data=sync_status[user_id],
            message='同步任务已提交'
        )
        
    except Exception as e:
        logger.error(f"同步失败: {str(e)}")
        sync_status[user_id] = {
            'status': 'error',
            'count': 0,
            'message': f'同步失败: {str(e)}'
        }
        return error_response(str(e), data=sync_status[user_id])
    finally:
        db.close()


@sync_bp.route('/task/sync-status', methods=['GET'])
@require_auth
def get_sync_status():
    """
    查询同步状态
    
    返回当前用户的同步任务状态
    """
    user_id = request.user_id
    
    status = sync_status.get(user_id, {
        'status': 'idle',
        'count': 0,
        'message': '暂无同步任务'
    })
    
    return success_response(data=status)


@sync_bp.route('/callback', methods=['POST'])
def douplus_callback():
    """
    DOU+平台回调接口
    
    接收平台的订单状态更新通知
    注意：此接口不需要JWT认证（平台回调）
    """
    try:
        data = request.json
        logger.info(f"收到DOU+回调: {data}")
        
        # TODO: 处理回调数据，更新订单状态
        # 可以触发增量同步任务
        
        return success_response(message='回调接收成功')
        
    except Exception as e:
        logger.error(f"处理回调失败: {str(e)}")
        return error_response(f"处理失败: {str(e)}")
