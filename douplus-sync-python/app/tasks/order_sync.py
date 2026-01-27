"""
订单同步任务
"""
from celery import Task
from datetime import datetime, timedelta
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import update
from loguru import logger

from app.models import DouyinAccount, DouplusOrder, SyncTaskLog, SyncTaskDetail, get_db
from app.douyin_client import DouyinClient, DouyinAPIError
from app.utils.crypto import decrypt_access_token
from app.config import get_settings


settings = get_settings()


class OrderSyncTask(Task):
    """订单同步任务基类"""
    
    def get_active_accounts(self):
        """获取所有活跃账号"""
        db = get_db()
        try:
            accounts = db.query(DouyinAccount).filter(
                DouyinAccount.status == 1
            ).all()
            return accounts
        finally:
            db.close()
    
    def sync_account_orders(self, account_id: int, sync_mode: str = "incremental"):
        """
        同步单个账号的订单
        
        Args:
            account_id: 账号ID
            sync_mode: full(全量) / incremental(增量)
        """
        db = get_db()
        try:
            # 1. 获取账号信息
            account = db.query(DouyinAccount).filter(
                DouyinAccount.id == account_id
            ).first()
            
            if not account:
                logger.warning(f"账号不存在: account_id={account_id}")
                return
            
            # 2. 解密AccessToken
            try:
                access_token = decrypt_access_token(account.access_token)
            except Exception as e:
                logger.error(f"解密token失败: account_id={account_id}, error={e}")
                return
            
            # 3. 创建API客户端
            client = DouyinClient(access_token)
            
            try:
                # 4. 获取订单列表(分页)
                page = 1
                page_size = 100
                total_synced = 0
                
                while True:
                    orders = client.get_order_list(
                        aweme_sec_uid=account.aweme_sec_uid,
                        page=page,
                        page_size=page_size
                    )
                    
                    if not orders:
                        break
                    
                    # 5. 批量插入/更新订单
                    for order_data in orders:
                        try:
                            self._upsert_order(db, order_data, account)
                            total_synced += 1
                        except Exception as e:
                            logger.error(f"保存订单失败: order_id={order_data.get('order_id')}, error={e}")
                    
                    db.commit()
                    
                    # 如果返回数量小于page_size,说明已经是最后一页
                    if len(orders) < page_size:
                        break
                    
                    page += 1
                
                logger.info(f"账号{account_id}订单同步完成: 共{total_synced}条")
                
            finally:
                client.close()
                
        except DouyinAPIError as e:
            logger.error(f"抖音API调用失败: account_id={account_id}, error={e}")
            db.rollback()
        except Exception as e:
            logger.error(f"订单同步异常: account_id={account_id}, error={e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    def sync_account_orders_with_count(self, account_id: int, sync_mode: str = "incremental") -> int:
        """
        同步单个账号的订单（返回同步数量）
        
        Args:
            account_id: 账号ID
            sync_mode: full(全量) / incremental(增量)
            
        Returns:
            同步的订单数量
        """
        db = get_db()
        total_synced = 0
        
        try:
            # 1. 获取账号信息
            account = db.query(DouyinAccount).filter(
                DouyinAccount.id == account_id
            ).first()
            
            if not account:
                logger.warning(f"账号不存在: account_id={account_id}")
                return 0
            
            # 2. 解密AccessToken
            try:
                access_token = decrypt_access_token(account.access_token)
            except Exception as e:
                logger.error(f"解密token失败: account_id={account_id}, error={e}")
                return 0
            
            # 3. 创建API客户端
            client = DouyinClient(access_token)
            
            try:
                # 4. 获取订单列表(分页)
                page = 1
                page_size = 100
                
                while True:
                    orders = client.get_order_list(
                        aweme_sec_uid=account.aweme_sec_uid,
                        page=page,
                        page_size=page_size
                    )
                    
                    if not orders:
                        break
                    
                    # 5. 批量插入/更新订单
                    for order_data in orders:
                        try:
                            self._upsert_order(db, order_data, account)
                            total_synced += 1
                        except Exception as e:
                            logger.error(f"保存订单失败: order_id={order_data.get('order_id')}, error={e}")
                    
                    db.commit()
                    
                    # 如果返回数量小于page_size,说明已经是最后一页
                    if len(orders) < page_size:
                        break
                    
                    page += 1
                
                logger.info(f"账号{account_id}订单同步完成: 共{total_synced}条")
                return total_synced
                
            finally:
                client.close()
                
        except DouyinAPIError as e:
            logger.error(f"抖音API调用失败: account_id={account_id}, error={e}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"订单同步异常: account_id={account_id}, error={e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
    
    def _upsert_order(self, db, order_data: dict, account: DouyinAccount):
        """
        插入或更新订单
        
        Args:
            db: 数据库会话
            order_data: 订单数据（API返回的完整结构）
            account: 账号对象
        """
        # API返回的数据结构是嵌套的，需要从order字段中提取
        order_info = order_data.get("order", {})
        item_info_list = order_data.get("item_info_list", [])
        item_info = item_info_list[0] if item_info_list else {}
        
        # 解析时间
        order_create_time = None
        create_time_str = order_info.get("order_create_time")
        if create_time_str:
            try:
                order_create_time = datetime.strptime(
                    create_time_str, "%Y-%m-%d %H:%M:%S"
                )
            except:
                pass
        
        # 构建数据
        values = {
            "order_id": order_info.get("order_id"),
            "item_id": item_info.get("aweme_item_id"),
            "account_id": account.id,
            "user_id": account.user_id,
            "status": order_info.get("task_status"),
            "budget": order_info.get("budget", 0) / 100.0,  # 分转元
            "duration": 24,  # API未返回此字段，使用默认值
            "aweme_title": item_info.get("aweme_item_title"),
            "aweme_cover": item_info.get("aweme_item_cover", [""])[0] if item_info.get("aweme_item_cover") else None,
            "aweme_nick": item_info.get("aweme_author_name"),
            "aweme_avatar": item_info.get("aweme_author_avatar", [""])[0] if item_info.get("aweme_author_avatar") else None,
            "order_create_time": order_create_time,
            "sync_version": 1,
            "last_sync_time": datetime.now(),
            "sync_source": "API",
        }
        
        # 使用INSERT ... ON DUPLICATE KEY UPDATE
        stmt = insert(DouplusOrder).values(**values)
        stmt = stmt.on_duplicate_key_update(
            account_id=values["account_id"],  # 重要：更新account_id，支持账号重新绑定
            status=values["status"],
            aweme_title=values["aweme_title"],
            aweme_cover=values["aweme_cover"],
            sync_version=DouplusOrder.sync_version + 1,
            last_sync_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.execute(stmt)


# Celery任务装饰器会在celery_app.py中应用
def sync_all_accounts_incremental():
    """增量同步所有账号的订单"""
    task = OrderSyncTask()
    accounts = task.get_active_accounts()
    
    logger.info(f"开始增量同步订单: 共{len(accounts)}个账号")
    
    for account in accounts:
        try:
            task.sync_account_orders(account.id, "incremental")
        except Exception as e:
            logger.error(f"账号{account.id}同步失败: {e}")
    
    logger.info("增量同步完成")


def sync_all_accounts_full():
    """全量同步所有账号的订单"""
    task = OrderSyncTask()
    accounts = task.get_active_accounts()
    
    logger.info(f"开始全量同步订单: 共{len(accounts)}个账号")
    
    for account in accounts:
        try:
            task.sync_account_orders(account.id, "full")
        except Exception as e:
            logger.error(f"账号{account.id}同步失败: {e}")
    
    logger.info("全量同步完成")


def sync_single_account(account_id: int, sync_mode: str = "incremental", task_id: int = None):
    """
    同步单个账号
    
    Args:
        account_id: 账号ID
        sync_mode: 同步模式 (full/incremental)
        task_id: 同步任务ID（可选，用于更新任务状态）
    """
    db = get_db()
    detail = None
    
    try:
        # 如果有task_id，更新明细状态为running
        if task_id:
            detail = db.query(SyncTaskDetail).filter(
                SyncTaskDetail.task_id == task_id,
                SyncTaskDetail.account_id == account_id
            ).first()
            
            if detail:
                detail.status = 'running'
                detail.start_time = datetime.now()
                db.commit()
        
        # 执行同步
        task = OrderSyncTask()
        total_synced = task.sync_account_orders_with_count(account_id, sync_mode)
        
        # 更新明细状态为completed
        if detail:
            detail.status = 'completed'
            detail.record_count = total_synced
            detail.end_time = datetime.now()
            db.commit()
            
            # 更新主任务统计
            _update_task_progress(db, task_id)
        
        logger.info(f"账号{account_id}同步任务完成: 共{total_synced}条")
        
    except Exception as e:
        logger.error(f"账号{account_id}同步失败: {e}", exc_info=True)
        
        # 更新明细状态为failed
        if detail:
            detail.status = 'failed'
            detail.error_message = str(e)
            detail.end_time = datetime.now()
            db.commit()
            
            # 更新主任务统计
            _update_task_progress(db, task_id)
        
        raise
    finally:
        db.close()


def _update_task_progress(db, task_id: int):
    """
    更新任务进度
    
    Args:
        db: 数据库会话
        task_id: 任务ID
    """
    if not task_id:
        return
    
    # 查询任务
    task = db.query(SyncTaskLog).filter(SyncTaskLog.id == task_id).first()
    if not task:
        return
    
    # 查询明细统计
    details = db.query(SyncTaskDetail).filter(SyncTaskDetail.task_id == task_id).all()
    
    completed = sum(1 for d in details if d.status in ['completed', 'failed'])
    success = sum(1 for d in details if d.status == 'completed')
    failed = sum(1 for d in details if d.status == 'failed')
    total_records = sum(d.record_count for d in details if d.record_count)
    
    # 更新任务
    task.completed_accounts = completed
    task.success_count = success
    task.fail_count = failed
    task.total_records = total_records
    
    # 判断是否全部完成
    if completed >= task.total_accounts:
        task.status = 'completed' if failed == 0 else 'failed'
        task.end_time = datetime.now()
        if failed > 0:
            task.error_message = f'{failed}个账号同步失败'
    
    db.commit()
    logger.info(f"任务{task_id}进度更新: {completed}/{task.total_accounts}, 成功{success}, 失败{failed}")
