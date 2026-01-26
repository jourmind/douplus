"""
订单同步任务
"""
from celery import Task
from datetime import datetime, timedelta
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import update
from loguru import logger

from app.models import DouyinAccount, DouplusOrder, get_db
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
    
    def _upsert_order(self, db, order_data: dict, account: DouyinAccount):
        """
        插入或更新订单
        
        Args:
            db: 数据库会话
            order_data: 订单数据
            account: 账号对象
        """
        # 解析时间
        order_create_time = None
        if order_data.get("create_time"):
            try:
                order_create_time = datetime.strptime(
                    order_data["create_time"], "%Y-%m-%d %H:%M:%S"
                )
            except:
                pass
        
        # 构建数据
        values = {
            "order_id": order_data.get("order_id"),
            "item_id": order_data.get("aweme_id"),
            "account_id": account.id,
            "user_id": account.user_id,
            "status": order_data.get("status"),
            "budget": order_data.get("budget", 0) / 100.0,  # 分转元
            "duration": order_data.get("duration", 24),
            "aweme_title": order_data.get("aweme_title"),
            "aweme_cover": order_data.get("aweme_cover"),
            "aweme_nick": order_data.get("aweme_nick"),
            "aweme_avatar": order_data.get("aweme_avatar"),
            "order_create_time": order_create_time,
            "sync_version": 1,
            "last_sync_time": datetime.now(),
            "sync_source": "API",
        }
        
        # 使用INSERT ... ON DUPLICATE KEY UPDATE
        stmt = insert(DouplusOrder).values(**values)
        stmt = stmt.on_duplicate_key_update(
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


def sync_single_account(account_id: int, sync_mode: str = "incremental"):
    """
    同步单个账号
    
    Args:
        account_id: 账号ID
        sync_mode: 同步模式
    """
    task = OrderSyncTask()
    task.sync_account_orders(account_id, sync_mode)
