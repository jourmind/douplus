"""
数据迁移脚本：douplus_task → douplus_order

功能：
1. 将旧表(douplus_task)的订单基础数据迁移到新表(douplus_order)
2. 保留order_id映射关系，确保幂等性
3. 支持增量迁移和全量迁移

执行方式：
python3 migrate_to_new_tables.py [--full]

参数：
--full: 全量迁移（清空新表后重新迁移所有数据）
不带参数: 增量迁移（只迁移新增或更新的数据）
"""
import sys
import argparse
from sqlalchemy import text
from datetime import datetime
from loguru import logger
from app.models import get_db
from app.utils.time_window import get_current_window


def migrate_orders_to_new_table(full_migration: bool = False):
    """
    迁移订单数据到新表
    
    Args:
        full_migration: 是否全量迁移（清空新表）
    """
    db = get_db()
    try:
        logger.info(f"开始{'全量' if full_migration else '增量'}迁移订单数据")
        
        # 1. 如果是全量迁移，先清空新表
        if full_migration:
            logger.warning("执行全量迁移：清空 douplus_order 表")
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            db.execute(text("TRUNCATE TABLE douplus_order"))
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            db.commit()
            logger.info("douplus_order 表已清空")
        
        # 2. 查询旧表数据统计
        old_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT user_id) as users,
                COUNT(DISTINCT account_id) as accounts,
                COUNT(DISTINCT item_id) as videos
            FROM douplus_task
            WHERE deleted = 0
        """)).fetchone()
        
        logger.info(f"旧表(douplus_task)统计: {old_stats[0]}个订单, {old_stats[1]}个用户, {old_stats[2]}个账号, {old_stats[3]}个视频")
        
        # 3. 执行迁移（使用INSERT ... ON DUPLICATE KEY UPDATE确保幂等性）
        migration_sql = text("""
            INSERT INTO douplus_order (
                order_id, item_id, account_id, user_id,
                status, budget, duration, target_type,
                aweme_title, aweme_cover, aweme_nick, aweme_avatar,
                order_create_time, order_start_time, order_end_time,
                sync_version, last_sync_time, sync_source,
                create_time, update_time, deleted
            )
            SELECT 
                order_id,
                item_id,
                account_id,
                user_id,
                status,
                budget,
                duration,
                CASE target_type
                    WHEN 1 THEN 'VIDEO'
                    WHEN 2 THEN 'LIVE'
                    ELSE 'VIDEO'
                END as target_type,
                video_title as aweme_title,
                video_cover_url as aweme_cover,
                aweme_nick,
                aweme_avatar,
                scheduled_time as order_create_time,
                executed_time as order_start_time,
                completed_time as order_end_time,
                1 as sync_version,
                update_time as last_sync_time,
                'MIGRATED' as sync_source,
                create_time,
                update_time,
                deleted
            FROM douplus_task
            WHERE deleted = 0
              AND order_id IS NOT NULL
              AND order_id != ''
            
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                aweme_title = VALUES(aweme_title),
                aweme_cover = VALUES(aweme_cover),
                sync_version = douplus_order.sync_version + 1,
                last_sync_time = NOW(),
                update_time = NOW()
        """)
        
        result = db.execute(migration_sql)
        db.commit()
        
        affected_rows = result.rowcount
        logger.info(f"订单数据迁移完成: 处理了{affected_rows}条记录")
        
        # 4. 验证迁移结果
        new_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT user_id) as users,
                COUNT(DISTINCT account_id) as accounts,
                COUNT(DISTINCT item_id) as videos
            FROM douplus_order
            WHERE deleted = 0
        """)).fetchone()
        
        logger.info(f"新表(douplus_order)统计: {new_stats[0]}个订单, {new_stats[1]}个用户, {new_stats[2]}个账号, {new_stats[3]}个视频")
        
        # 5. 对比验证
        if old_stats[0] == new_stats[0]:
            logger.info("✅ 数据完整性验证通过：新旧表订单数量一致")
        else:
            logger.warning(f"⚠️ 数据差异：旧表{old_stats[0]}条，新表{new_stats[0]}条，差异{old_stats[0] - new_stats[0]}条")
        
        return {
            'success': True,
            'old_count': old_stats[0],
            'new_count': new_stats[0],
            'affected': affected_rows
        }
        
    except Exception as e:
        logger.error(f"数据迁移失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def migrate_stats_metadata():
    """
    迁移效果数据元信息（从douplus_task提取到douplus_order_stats）
    
    注意：这是临时方案，正式流程应该从API获取实时效果数据
    """
    db = get_db()
    try:
        logger.info("开始迁移效果数据元信息")
        
        current_window = get_current_window()
        
        # 从douplus_task提取效果数据到douplus_order_stats
        stats_sql = text("""
            INSERT INTO douplus_order_stats (
                order_id, item_id, stat_time,
                stat_cost, total_play, custom_like, dy_comment, dy_share, dy_follow,
                play_duration_5s_rank, dy_home_visited, dp_target_convert_cnt, custom_convert_cost,
                show_cnt, live_click_source_cnt, live_gift_uv, live_gift_amount,
                live_comment_cnt, live_follow_count, live_gift_cnt,
                sync_time, create_time, update_time
            )
            SELECT 
                order_id,
                item_id,
                :stat_time as stat_time,
                actual_cost as stat_cost,
                play_count as total_play,
                like_count as custom_like,
                comment_count as dy_comment,
                share_count as dy_share,
                follow_count as dy_follow,
                play_duration_5s_rank,
                dy_home_visited,
                dp_target_convert_cnt,
                custom_convert_cost,
                show_cnt,
                live_click_source_cnt,
                live_gift_uv,
                live_gift_amount,
                live_comment_cnt,
                douplus_live_follow_count as live_follow_count,
                live_gift_cnt,
                NOW() as sync_time,
                NOW() as create_time,
                NOW() as update_time
            FROM douplus_task
            WHERE deleted = 0
              AND order_id IS NOT NULL
              AND order_id != ''
            
            ON DUPLICATE KEY UPDATE
                stat_cost = VALUES(stat_cost),
                total_play = VALUES(total_play),
                custom_like = VALUES(custom_like),
                dy_comment = VALUES(dy_comment),
                dy_share = VALUES(dy_share),
                dy_follow = VALUES(dy_follow),
                sync_time = NOW(),
                update_time = NOW()
        """)
        
        result = db.execute(stats_sql, {'stat_time': current_window})
        db.commit()
        
        affected_rows = result.rowcount
        logger.info(f"效果数据迁移完成: 处理了{affected_rows}条记录")
        
        # 验证
        count = db.execute(text("SELECT COUNT(*) FROM douplus_order_stats")).fetchone()[0]
        logger.info(f"douplus_order_stats 表当前有 {count} 条记录")
        
        return affected_rows
        
    except Exception as e:
        logger.error(f"效果数据迁移失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def rebuild_video_agg_from_new_tables():
    """
    从新表重建视频预聚合表
    """
    logger.info("从新表结构重建视频预聚合表")
    
    from app.tasks.video_agg import rebuild_video_agg_table
    
    try:
        rebuild_video_agg_table()
        logger.info("✅ 视频预聚合表重建完成")
    except Exception as e:
        logger.error(f"❌ 视频预聚合表重建失败: {e}")
        raise


if __name__ == '__main__':
    sys.path.insert(0, '/opt/douplus/douplus-sync-python')
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='数据迁移脚本')
    parser.add_argument('--full', action='store_true', help='全量迁移（清空新表）')
    parser.add_argument('--stats-only', action='store_true', help='只迁移效果数据')
    parser.add_argument('--rebuild-agg', action='store_true', help='重建预聚合表')
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOU+订单管理系统 - 数据迁移工具")
    print("=" * 70)
    print()
    
    if args.stats_only:
        print("模式：仅迁移效果数据")
        print()
        try:
            count = migrate_stats_metadata()
            print()
            print(f"✅ 效果数据迁移完成: {count} 条记录")
            print()
        except Exception as e:
            print()
            print(f"❌ 迁移失败: {e}")
            print()
            sys.exit(1)
    
    elif args.rebuild_agg:
        print("模式：重建预聚合表")
        print()
        try:
            rebuild_video_agg_from_new_tables()
            print()
            print("✅ 预聚合表重建完成")
            print()
        except Exception as e:
            print()
            print(f"❌ 重建失败: {e}")
            print()
            sys.exit(1)
    
    else:
        mode = "全量迁移" if args.full else "增量迁移"
        print(f"模式：{mode}")
        print()
        print("迁移步骤：")
        print("1. 迁移订单基础数据 (douplus_task → douplus_order)")
        print("2. 迁移效果数据 (douplus_task → douplus_order_stats)")
        print("3. 重建视频预聚合表 (douplus_video_stats_agg)")
        print()
        
        if args.full:
            print("⚠️  警告：全量迁移将清空新表的所有数据！")
            print()
            confirm = input("确认执行全量迁移？(yes/no): ")
            if confirm.lower() != 'yes':
                print("已取消")
                sys.exit(0)
            print()
        
        try:
            # 步骤1: 迁移订单
            print("步骤1: 迁移订单基础数据...")
            order_result = migrate_orders_to_new_table(args.full)
            print(f"✅ 订单迁移完成: {order_result['new_count']} 条订单")
            print()
            
            # 步骤2: 迁移效果数据
            print("步骤2: 迁移效果数据...")
            stats_count = migrate_stats_metadata()
            print(f"✅ 效果数据迁移完成: {stats_count} 条记录")
            print()
            
            # 步骤3: 重建预聚合表
            print("步骤3: 重建视频预聚合表...")
            rebuild_video_agg_from_new_tables()
            print("✅ 预聚合表重建完成")
            print()
            
            print("=" * 70)
            print("🎉 数据迁移全部完成！")
            print("=" * 70)
            print()
            print("迁移统计：")
            print(f"  - 订单数量: {order_result['new_count']}")
            print(f"  - 效果记录: {stats_count}")
            print()
            print("下一步：")
            print("1. 重启Python服务以应用新的数据结构")
            print("2. 测试前端页面确认数据正常显示")
            print("3. 观察后台同步任务是否正常写入新表")
            print()
            
        except Exception as e:
            print()
            print(f"❌ 迁移失败: {e}")
            print()
            import traceback
            traceback.print_exc()
            sys.exit(1)
