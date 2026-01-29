"""
数据库ORM模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, DECIMAL, Float, Text, create_engine, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from app.config import get_settings

Base = declarative_base()

# 数据库引擎
settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # 由调用者负责关闭


class SysUser(Base):
    """系统用户表"""
    __tablename__ = 'sys_user'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50))
    avatar = Column(String(255))
    email = Column(String(100))
    phone = Column(String(20))
    invest_password = Column(String(255))
    status = Column(SmallInteger, default=1)
    last_login_time = Column(DateTime)
    last_login_ip = Column(String(50))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted = Column(Integer, default=0)


class DouyinAccount(Base):
    """抖音账号表"""
    __tablename__ = 'douyin_account'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    open_id = Column(String(100))
    advertiser_id = Column(String(100))
    aweme_sec_uid = Column(String(200), index=True)
    advertiser_name = Column(String(100))
    union_id = Column(String(100))
    nickname = Column(String(100))
    avatar = Column(String(500))
    fans_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    total_favorited = Column(Integer, default=0)
    access_token = Column(Text)  # Base64加密
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    status = Column(Integer, default=1, index=True)
    daily_limit = Column(DECIMAL(10, 2), default=10000)
    balance = Column(DECIMAL(10, 2), default=0)
    remark = Column(String(500))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted = Column(Integer, default=0)


class DouplusOrder(Base):
    """DOU+订单基础表"""
    __tablename__ = 'douplus_order'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(64), unique=True, nullable=False, index=True)
    task_id = Column(String(64), index=True)  # DOU+后台订单号(PC端可见)
    item_id = Column(String(64), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    
    status = Column(String(32))
    budget = Column(DECIMAL(10, 2), default=0)
    duration = Column(Integer, default=24)
    target_type = Column(String(32))
    
    aweme_title = Column(String(500))
    aweme_cover = Column(String(500))
    aweme_nick = Column(String(100))
    aweme_avatar = Column(String(500))
    
    order_create_time = Column(DateTime)
    order_start_time = Column(DateTime)
    order_end_time = Column(DateTime)
    
    sync_version = Column(BigInteger, default=0)
    last_sync_time = Column(DateTime)
    sync_source = Column(String(32), default='API')
    
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted = Column(Integer, default=0)


class DouplusOrderStats(Base):
    """DOU+订单效果数据明细表"""
    __tablename__ = 'douplus_order_stats'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(64), nullable=False, index=True)
    item_id = Column(String(64), nullable=False, index=True)
    
    stat_time = Column(DateTime, nullable=False, index=True)
    
    stat_cost = Column(DECIMAL(10, 2), default=0)
    total_play = Column(Integer, default=0)
    custom_like = Column(Integer, default=0)
    dy_comment = Column(Integer, default=0)
    dy_share = Column(Integer, default=0)
    dy_follow = Column(Integer, default=0)
    
    play_duration_5s_rank = Column(Float, default=0)
    dy_home_visited = Column(Integer, default=0)
    dp_target_convert_cnt = Column(Integer, default=0)
    custom_convert_cost = Column(DECIMAL(10, 2), default=0)
    
    show_cnt = Column(Integer, default=0)
    live_click_source_cnt = Column(Integer, default=0)
    live_gift_uv = Column(Integer, default=0)
    live_gift_amount = Column(DECIMAL(10, 2), default=0)
    live_comment_cnt = Column(Integer, default=0)
    live_follow_count = Column(Integer, default=0)
    live_gift_cnt = Column(Integer, default=0)
    
    sync_time = Column(DateTime)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DouplusOrderAgg(Base):
    """DOU+订单维度预聚合表"""
    __tablename__ = 'douplus_order_agg'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(64), unique=True, nullable=False, index=True)
    item_id = Column(String(64), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    
    # 原始指标
    total_cost = Column(DECIMAL(10, 2), default=0)
    total_play = Column(Integer, default=0)
    total_like = Column(Integer, default=0)
    total_comment = Column(Integer, default=0)
    total_share = Column(Integer, default=0)
    total_follow = Column(Integer, default=0)
    total_convert = Column(Integer, default=0)
    play_duration_5s = Column(Float, default=0)
    
    # 预聚合计算指标
    play_per_100_cost = Column(DECIMAL(10, 2), default=0, index=True)  # 百播放量
    avg_convert_cost = Column(DECIMAL(10, 2), index=True)  # 转化成本(可为NULL)
    share_rate = Column(DECIMAL(10, 4), default=0)  # 百转发率
    like_rate = Column(DECIMAL(10, 4), default=0)  # 点赞比
    follow_rate = Column(DECIMAL(10, 4), default=0)  # 转发比
    
    stat_time = Column(DateTime, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DouplusVideoStatsAgg(Base):
    """视频维度效果预聚合表"""
    __tablename__ = 'douplus_video_stats_agg'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(String(64), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    
    stat_time = Column(DateTime, nullable=False, index=True)
    
    order_count = Column(Integer, default=0)
    total_budget = Column(DECIMAL(10, 2), default=0)
    total_cost = Column(DECIMAL(10, 2), default=0)
    total_play = Column(BigInteger, default=0)
    total_like = Column(BigInteger, default=0)
    total_comment = Column(BigInteger, default=0)
    total_share = Column(BigInteger, default=0)
    total_follow = Column(BigInteger, default=0)
    total_convert = Column(BigInteger, default=0)
    total_home_visited = Column(BigInteger, default=0)
    
    avg_5s_rank = Column(Float)
    avg_convert_cost = Column(DECIMAL(10, 2))
    
    play_per_100_cost = Column(DECIMAL(10, 2))
    like_rate = Column(DECIMAL(10, 4))
    share_rate = Column(DECIMAL(10, 4))
    share_per_100_play = Column(DECIMAL(10, 2))
    
    agg_time = Column(DateTime)
    data_version = Column(BigInteger, default=1)
    
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SyncTaskLog(Base):
    """同步任务日志表"""
    __tablename__ = 'sync_task_log'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    task_type = Column(String(20), nullable=False)  # order/stats
    sync_mode = Column(String(20))  # full/incremental
    status = Column(String(20), nullable=False, default='pending')  # pending/running/completed/failed
    total_accounts = Column(Integer, default=0)
    completed_accounts = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    error_message = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    celery_task_id = Column(String(255))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SyncTaskDetail(Base):
    """同步任务明细表"""
    __tablename__ = 'sync_task_detail'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    account_id = Column(BigInteger, nullable=False)
    account_name = Column(String(100))
    status = Column(String(20), nullable=False, default='pending')  # pending/running/completed/failed
    record_count = Column(Integer, default=0)
    error_message = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
