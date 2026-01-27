"""
Celery应用配置
"""
from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

# 创建Celery应用
app = Celery(
    'douplus_sync',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery配置
app.conf.update(
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区配置
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务配置
    task_track_started=True,
    task_time_limit=3600,  # 任务最长执行时间1小时
    task_soft_time_limit=3000,  # 软限制50分钟
    
    # 结果过期时间
    result_expires=3600,
    
    # Worker配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由配置（暂时禁用，使用默认队列）
# app.conf.task_routes = {
#     'app.tasks.order_sync.*': {'queue': 'order_sync'},
#     'app.tasks.stats_sync.*': {'queue': 'stats_sync'},
#     'app.tasks.video_agg.*': {'queue': 'video_agg'},
# }

# 定时任务配置
app.conf.beat_schedule = {
    # 每5分钟增量同步订单
    'sync-orders-incremental': {
        'task': 'app.tasks.order_sync.sync_all_accounts_incremental',
        'schedule': crontab(minute='*/5'),
    },
    
    # 每5分钟同步效果数据(延迟1分钟,确保订单已同步)
    'sync-stats': {
        'task': 'app.tasks.stats_sync.sync_all_accounts_stats',
        'schedule': crontab(minute='1-59/5'),  # 1,6,11,16...
    },
    
    # 每5分钟聚合视频数据(延迟2分钟,确保效果数据已同步)
    'aggregate-video': {
        'task': 'app.tasks.video_agg.aggregate_current_window',
        'schedule': crontab(minute='2-59/5'),  # 2,7,12,17...
    },
    
    # 每天凌晨2点自动刷新即将过期的Token
    'refresh-expiring-tokens': {
        'task': 'app.tasks.token_refresh.refresh_expiring_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
}

# 自动发现任务
app.autodiscover_tasks(['app.tasks'])

# 注册任务
from app.tasks.order_sync import (
    sync_all_accounts_incremental,
    sync_all_accounts_full,
    sync_single_account
)
from app.tasks.stats_sync import (
    sync_all_accounts_stats,
    sync_single_account_stats
)
from app.tasks.video_agg import (
    aggregate_current_window,
    aggregate_all_recent,
    rebuild_video_agg_table
)
from app.tasks.token_refresh import (
    refresh_expiring_tokens,
    refresh_single_account_token
)

# 将函数注册为Celery任务
app.task(name='app.tasks.order_sync.sync_all_accounts_incremental')(sync_all_accounts_incremental)
app.task(name='app.tasks.order_sync.sync_all_accounts_full')(sync_all_accounts_full)
app.task(name='app.tasks.order_sync.sync_single_account')(sync_single_account)
app.task(name='app.tasks.stats_sync.sync_all_accounts_stats')(sync_all_accounts_stats)
app.task(name='app.tasks.stats_sync.sync_single_account_stats')(sync_single_account_stats)
app.task(name='app.tasks.video_agg.aggregate_current_window')(aggregate_current_window)
app.task(name='app.tasks.video_agg.aggregate_all_recent')(aggregate_all_recent)
app.task(name='app.tasks.video_agg.rebuild_video_agg_table')(rebuild_video_agg_table)
app.task(name='app.tasks.token_refresh.refresh_expiring_tokens')(refresh_expiring_tokens)
app.task(name='app.tasks.token_refresh.refresh_single_account_token')(refresh_single_account_token)
