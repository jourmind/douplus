"""
效果数据同步任务
"""
from celery import Task
from datetime import datetime, timedelta
from sqlalchemy.dialects.mysql import insert
from loguru import logger

from app.models import DouyinAccount, DouplusOrder, DouplusOrderStats, get_db
from app.douyin_client import DouyinClient, DouyinAPIError
from app.utils.crypto import decrypt_access_token
from app.utils.time_window import get_current_window
from app.config import get_settings


settings = get_settings()


class StatsSyncTask(Task):
    """效果数据同步任务基类"""
    
    def sync_account_stats(self, account_id: int):
        """
        同步单个账号的效果数据
        
        Args:
            account_id: 账号ID
        """
        db = get_db()
        try:
            # 1. 获取账号
            account = db.query(DouyinAccount).filter(
                DouyinAccount.id == account_id
            ).first()
            
            if not account:
                logger.warning(f"账号不存在: account_id={account_id}")
                return
            
            # 2. 获取需要同步效果数据的订单(最近7天有更新的)
            cutoff_time = datetime.now() - timedelta(days=settings.SYNC_INCREMENTAL_DAYS)
            orders = db.query(DouplusOrder).filter(
                DouplusOrder.account_id == account_id,
                DouplusOrder.last_sync_time >= cutoff_time
            ).all()
            
            if not orders:
                logger.info(f"账号{account_id}没有需要同步效果数据的订单")
                return
            
            logger.info(f"账号{account_id}需要同步{len(orders)}个订单的效果数据")
            
            # 3. 解密Token并创建客户端
            try:
                access_token = decrypt_access_token(account.access_token)
            except Exception as e:
                logger.error(f"解密token失败: account_id={account_id}, error={e}")
                return
            
            client = DouyinClient(access_token)
            
            try:
                # 4. 调用效果报告API（按订单ID批量查询，避免时间范围查询漏数据）
                # stat_time参数设置为覆盖所有可能的时间范围
                current_month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
                current_month_end = (datetime.now() + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")
                
                # 提取订单ID列表
                order_ids = [o.order_id for o in orders]
                
                # API限制：每次最多查询100个订单，需要分批查询
                batch_size = 100
                stats_dict = {}
                
                for i in range(0, len(order_ids), batch_size):
                    batch = order_ids[i:i+batch_size]
                    logger.info(f"查询第{i//batch_size + 1}批订单效果数据: {len(batch)}个订单")
                    
                    batch_stats = client.get_order_report(
                        aweme_sec_uid=account.aweme_sec_uid,
                        begin_time=current_month_start,
                        end_time=current_month_end,
                        order_ids=batch
                    )
                    stats_dict.update(batch_stats)
                
                if not stats_dict:
                    logger.info(f"账号{account_id}未获取到效果数据")
                    return
                
                # 5. 保存效果数据
                stat_time = get_current_window()
                total_saved = 0
                
                for order_id, stats_data in stats_dict.items():
                    try:
                        self._upsert_stats(db, stats_data, stat_time)
                        total_saved += 1
                    except Exception as e:
                        logger.error(f"保存效果数据失败: order_id={order_id}, error={e}")
                
                db.commit()
                logger.info(f"账号{account_id}效果数据同步完成: 共{total_saved}条")
                
                # 【预聚合优化】同步完成后更新订单预聚合表，提升查询性能
                try:
                    from app.tasks.order_agg import aggregate_single_account_orders
                    aggregate_single_account_orders(account_id)
                except Exception as e:
                    logger.error(f"账号{account_id}订单预聚合失败: {e}")
                    # 预聚合失败不影响主流程
                
            finally:
                client.close()
                
        except DouyinAPIError as e:
            logger.error(f"抖音API调用失败: account_id={account_id}, error={e}")
            db.rollback()
        except Exception as e:
            logger.error(f"效果数据同步异常: account_id={account_id}, error={e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    def _upsert_stats(self, db, stats_data: dict, stat_time: datetime):
        """
        插入或更新效果数据
        
        Args:
            db: 数据库会话
            stats_data: 效果数据
            stat_time: 统计时间
        """
        # item_id必填，如果API没返回就从订单表查询
        item_id = stats_data.get("item_id")
        if not item_id:
            order = db.query(DouplusOrder).filter_by(order_id=stats_data["order_id"]).first()
            if order:
                item_id = order.item_id
            else:
                item_id = ''  # 兜底值
        
        values = {
            "order_id": stats_data["order_id"],
            "item_id": item_id,
            "stat_time": stat_time,
            "stat_cost": stats_data.get("stat_cost", 0),
            "total_play": stats_data.get("total_play", 0),
            "custom_like": stats_data.get("custom_like", 0),
            "dy_comment": stats_data.get("dy_comment", 0),
            "dy_share": stats_data.get("dy_share", 0),
            "dy_follow": stats_data.get("dy_follow", 0),
            "play_duration_5s_rank": stats_data.get("play_duration_5s_rank", 0),
            "dy_home_visited": stats_data.get("dy_home_visited", 0),
            "dp_target_convert_cnt": stats_data.get("dp_target_convert_cnt", 0),
            "custom_convert_cost": stats_data.get("custom_convert_cost", 0),
            "show_cnt": stats_data.get("show_cnt", 0),
            "live_click_source_cnt": stats_data.get("live_click_source_cnt", 0),
            "live_gift_uv": stats_data.get("live_gift_uv", 0),
            "live_gift_amount": stats_data.get("live_gift_amount", 0),
            "live_comment_cnt": stats_data.get("live_comment_cnt", 0),
            "live_follow_count": stats_data.get("live_follow_count", 0),
            "live_gift_cnt": stats_data.get("live_gift_cnt", 0),
            "sync_time": datetime.now(),
        }
        
        # INSERT ... ON DUPLICATE KEY UPDATE
        stmt = insert(DouplusOrderStats).values(**values)
        stmt = stmt.on_duplicate_key_update(
            stat_cost=values["stat_cost"],
            total_play=values["total_play"],
            custom_like=values["custom_like"],
            dy_comment=values["dy_comment"],
            dy_share=values["dy_share"],
            dy_follow=values["dy_follow"],
            play_duration_5s_rank=values["play_duration_5s_rank"],
            dy_home_visited=values["dy_home_visited"],
            dp_target_convert_cnt=values["dp_target_convert_cnt"],
            custom_convert_cost=values["custom_convert_cost"],
            sync_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.execute(stmt)


def sync_all_accounts_stats():
    """同步所有账号的效果数据"""
    db = get_db()
    try:
        accounts = db.query(DouyinAccount).filter(DouyinAccount.status == 1).all()
    finally:
        db.close()
    
    logger.info(f"开始同步效果数据: 共{len(accounts)}个账号")
    
    task = StatsSyncTask()
    for account in accounts:
        try:
            task.sync_account_stats(account.id)
        except Exception as e:
            logger.error(f"账号{account.id}效果数据同步失败: {e}")
    
    logger.info("效果数据同步完成")


def sync_single_account_stats(account_id: int):
    """同步单个账号的效果数据"""
    task = StatsSyncTask()
    task.sync_account_stats(account_id)
