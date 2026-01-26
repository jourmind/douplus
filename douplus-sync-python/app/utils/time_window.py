"""
时间窗口工具
"""
from datetime import datetime, timedelta


def round_to_5min(dt: datetime) -> datetime:
    """
    将时间向下取整到5分钟粒度
    
    Args:
        dt: 原始时间
    
    Returns:
        取整后的时间
    
    Examples:
        2026-01-26 12:07:35 → 2026-01-26 12:05:00
        2026-01-26 12:03:15 → 2026-01-26 12:00:00
        2026-01-26 12:13:59 → 2026-01-26 12:10:00
    """
    minute = dt.minute
    rounded_minute = (minute // 5) * 5
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)


def get_current_window() -> datetime:
    """获取当前时间的5分钟窗口"""
    return round_to_5min(datetime.now())


def get_previous_window() -> datetime:
    """获取上一个5分钟窗口"""
    return round_to_5min(datetime.now() - timedelta(minutes=5))
