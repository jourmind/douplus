"""
同步层API - 订单采集与历史同步

职责：
1. 触发订单同步（全量/增量）
2. 查询同步状态
3. 查询同步历史记录
4. DOU+平台回调接收

架构原则：
- 只负责数据采集，不做统计计算
- 调用Celery任务异步执行
- 返回任务提交状态
- 持久化任务状态到数据库
"""

import logging
from datetime import datetime
from flask import request
from sqlalchemy import text
from app.api import sync_bp
from app.api.common import require_auth, success_response, error_response, paginated_response
from app.models import SessionLocal, SyncTaskLog, SyncTaskDetail

logger = logging.getLogger(__name__)


@sync_bp.route('/task/sync-all', methods=['POST'])
@require_auth
def sync_all_orders():
    """
    同步所有账号的DOU+历史订单（全量同步）
    
    触发机制：用户点击"同步历史订单"按钮
    执行方式：异步Celery任务
    返回：任务ID，供后续状态查询
    """
    user_id = request.user_id
    
    logger.info(f"收到全量同步请求，用户ID: {user_id}")
    
    db = SessionLocal()
    try:
        # 1. 检查是否有正在进行的同步任务
        running_task = db.query(SyncTaskLog).filter(
            SyncTaskLog.user_id == user_id,
            SyncTaskLog.task_type == 'order',
            SyncTaskLog.status.in_(['pending', 'running'])
        ).first()
        
        if running_task:
            return success_response(
                data={
                    'taskId': running_task.id,
                    'status': running_task.status,
                    'progress': f"{running_task.completed_accounts}/{running_task.total_accounts}",
                    'message': '已有同步任务正在进行中'
                },
                message='正在同步中，请稍候...'
            )
        
        # 2. 获取该用户的所有账号
        query_sql = text("""
            SELECT id, advertiser_id, nickname
            FROM douyin_account
            WHERE user_id = :user_id AND status = 1 AND deleted = 0
        """)
        
        accounts = db.execute(query_sql, {'user_id': user_id}).fetchall()
        
        if not accounts:
            return error_response('没有可用的抖音账号', code=400)
        
        # 3. 创建同步任务记录
        task_log = SyncTaskLog(
            user_id=user_id,
            task_type='order',
            sync_mode='full',
            status='pending',
            total_accounts=len(accounts),
            completed_accounts=0,
            total_records=0,
            success_count=0,
            fail_count=0,
            start_time=datetime.now()
        )
        db.add(task_log)
        db.flush()  # 获取task_log.id
        
        # 4. 创建任务明细记录
        for account in accounts:
            detail = SyncTaskDetail(
                task_id=task_log.id,
                account_id=account[0],
                account_name=account[2],
                status='pending'
            )
            db.add(detail)
        
        db.commit()
        
        # 5. 异步触发每个账号的全量同步任务
        from celery_app import app as celery_app
        from celery import group
        
        # 更新任务状态为running
        task_log.status = 'running'
        db.commit()
        
        # 创建任务组
        tasks = []
        for account in accounts:
            account_id = account[0]
            task = celery_app.send_task(
                'app.tasks.order_sync.sync_single_account',
                args=[account_id, 'full', task_log.id]  # 传递task_id用于状态更新
            )
            tasks.append(task)
            logger.info(f"已提交账号{account_id}的全量同步任务到Celery队列, task_id={task_log.id}")
        
        return success_response(
            data={
                'taskId': task_log.id,
                'status': 'running',
                'totalAccounts': len(accounts),
                'message': f'同步任务已提交，共{len(accounts)}个账号'
            },
            message='同步任务已提交'
        )
        
    except Exception as e:
        logger.error(f"同步失败: {str(e)}")
        db.rollback()
        return error_response(str(e))
    finally:
        db.close()


@sync_bp.route('/task/sync-status/<int:task_id>', methods=['GET'])
@require_auth
def get_sync_task_status(task_id):
    """
    查询指定同步任务的状态
    
    参数：
    - task_id: 任务ID
    
    返回：任务状态、进度、详情
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 查询任务记录
        task = db.query(SyncTaskLog).filter(
            SyncTaskLog.id == task_id,
            SyncTaskLog.user_id == user_id
        ).first()
        
        if not task:
            return error_response('任务不存在', code=404)
        
        # 查询任务明细
        details = db.query(SyncTaskDetail).filter(
            SyncTaskDetail.task_id == task_id
        ).all()
        
        # 构造返回数据
        detail_list = []
        for detail in details:
            detail_list.append({
                'accountId': detail.account_id,
                'accountName': detail.account_name,
                'status': detail.status,
                'recordCount': detail.record_count,
                'errorMessage': detail.error_message,
                'startTime': detail.start_time.strftime('%Y-%m-%d %H:%M:%S') if detail.start_time else None,
                'endTime': detail.end_time.strftime('%Y-%m-%d %H:%M:%S') if detail.end_time else None
            })
        
        # 计算耗时
        duration = None
        if task.start_time:
            end_time = task.end_time if task.end_time else datetime.now()
            duration_seconds = (end_time - task.start_time).total_seconds()
            duration = f"{int(duration_seconds // 60)}分{int(duration_seconds % 60)}秒"
        
        return success_response({
            'taskId': task.id,
            'taskType': task.task_type,
            'syncMode': task.sync_mode,
            'status': task.status,
            'totalAccounts': task.total_accounts,
            'completedAccounts': task.completed_accounts,
            'totalRecords': task.total_records,
            'successCount': task.success_count,
            'failCount': task.fail_count,
            'errorMessage': task.error_message,
            'startTime': task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else None,
            'endTime': task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else None,
            'duration': duration,
            'progress': f"{task.completed_accounts}/{task.total_accounts}",
            'progressPercent': round(task.completed_accounts / task.total_accounts * 100, 1) if task.total_accounts > 0 else 0,
            'details': detail_list
        })
        
    except Exception as e:
        logger.error(f"查询同步状态失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@sync_bp.route('/task/sync-history', methods=['GET'])
@require_auth
def get_sync_history():
    """
    查询用户的同步历史记录
    
    参数：
    - taskType: 任务类型（order/stats），可选
    - pageNum: 页码
    - pageSize: 每页条数
    
    返回：同步任务列表
    """
    user_id = request.user_id
    task_type = request.args.get('taskType')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    db = SessionLocal()
    try:
        # 构建查询
        query = db.query(SyncTaskLog).filter(
            SyncTaskLog.user_id == user_id
        )
        
        if task_type:
            query = query.filter(SyncTaskLog.task_type == task_type)
        
        # 总数
        total = query.count()
        
        # 分页查询
        tasks = query.order_by(
            SyncTaskLog.create_time.desc()
        ).limit(page_size).offset((page_num - 1) * page_size).all()
        
        # 构造返回数据
        records = []
        for task in tasks:
            # 计算耗时
            duration = None
            if task.start_time:
                end_time = task.end_time if task.end_time else datetime.now()
                duration_seconds = (end_time - task.start_time).total_seconds()
                duration = f"{int(duration_seconds // 60)}分{int(duration_seconds % 60)}秒"
            
            records.append({
                'taskId': task.id,
                'taskType': task.task_type,
                'taskTypeName': '订单同步' if task.task_type == 'order' else '效果同步',
                'syncMode': task.sync_mode,
                'syncModeName': '全量' if task.sync_mode == 'full' else '增量',
                'status': task.status,
                'statusName': {
                    'pending': '等待中',
                    'running': '进行中',
                    'completed': '已完成',
                    'failed': '失败'
                }.get(task.status, task.status),
                'totalAccounts': task.total_accounts,
                'completedAccounts': task.completed_accounts,
                'totalRecords': task.total_records,
                'successCount': task.success_count,
                'failCount': task.fail_count,
                'progress': f"{task.completed_accounts}/{task.total_accounts}",
                'progressPercent': round(task.completed_accounts / task.total_accounts * 100, 1) if task.total_accounts > 0 else 0,
                'duration': duration,
                'createTime': task.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'errorMessage': task.error_message
            })
        
        return paginated_response(records, total, page_num, page_size)
        
    except Exception as e:
        logger.error(f"查询同步历史失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@sync_bp.route('/task/latest-status', methods=['GET'])
@sync_bp.route('/sync/status', methods=['GET'])  # 前端兼容路由
@require_auth
def get_latest_sync_status():
    """
    获取用户最新的同步任务状态（用于前端轮询）
    
    返回：最新任务的简要状态
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 查询最新的同步任务
        task = db.query(SyncTaskLog).filter(
            SyncTaskLog.user_id == user_id,
            SyncTaskLog.task_type == 'order'
        ).order_by(
            SyncTaskLog.create_time.desc()
        ).first()
        
        if not task:
            return success_response({
                'hasTask': False,
                'status': 'idle',
                'message': '暂无同步任务'
            })
        
        return success_response({
            'hasTask': True,
            'taskId': task.id,
            'status': task.status,
            'progress': f"{task.completed_accounts}/{task.total_accounts}",
            'progressPercent': round(task.completed_accounts / task.total_accounts * 100, 1) if task.total_accounts > 0 else 0,
            'totalRecords': task.total_records,
            'message': {
                'pending': '同步任务等待中...',
                'running': f'正在同步中，已完成 {task.completed_accounts}/{task.total_accounts} 个账号',
                'completed': f'同步完成！共同步 {task.total_records} 条订单',
                'failed': f'同步失败：{task.error_message}'
            }.get(task.status, '未知状态')
        })
        
    except Exception as e:
        logger.error(f"查询最新同步状态失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


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
