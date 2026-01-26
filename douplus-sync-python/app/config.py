"""
配置模块
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "douplus"
    DB_USER: str = "douplus"
    DB_PASSWORD: str = ""
    
    # Redis配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "/opt/douplus/douplus-sync-python/logs"
    
    # 同步配置
    SYNC_INCREMENTAL_DAYS: int = 7
    SYNC_FULL_DAYS: int = 90
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
