#!/usr/bin/env python3
"""
Python同步服务测试脚本
"""
import sys
sys.path.insert(0, '/opt/douplus/douplus-sync-python')

print("=" * 60)
print("DOU+ Python同步服务 - 代码测试")
print("=" * 60)
print()

# 测试1: 导入配置
print(">>> 测试1: 配置模块...")
try:
    from app.config import get_settings
    settings = get_settings()
    print(f"✓ 配置加载成功")
    print(f"  数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
except Exception as e:
    print(f"✗ 配置加载失败: {e}")
    sys.exit(1)
print()

# 测试2: 数据库模型
print(">>> 测试2: 数据库模型...")
try:
    from app.models import DouyinAccount, DouplusOrder, get_db
    print("✓ 模型导入成功")
    
    # 测试数据库连接
    db = get_db()
    count = db.query(DouyinAccount).filter(DouyinAccount.status == 1).count()
    db.close()
    print(f"✓ 数据库连接成功,活跃账号数: {count}")
except Exception as e:
    print(f"✗ 数据库测试失败: {e}")
    sys.exit(1)
print()

# 测试3: 工具类
print(">>> 测试3: 工具类...")
try:
    from app.utils.time_window import round_to_5min, get_current_window
    from app.utils.crypto import decrypt_access_token, encrypt_access_token
    from datetime import datetime
    
    # 测试时间窗口
    dt = datetime(2026, 1, 26, 12, 7, 35)
    rounded = round_to_5min(dt)
    assert rounded.minute == 5, "时间窗口取整错误"
    print(f"✓ 时间窗口工具正常: {dt} → {rounded}")
    
    # 测试加密解密
    token = "test_token_123"
    encrypted = encrypt_access_token(token)
    decrypted = decrypt_access_token(encrypted)
    assert decrypted == token, "加密解密不匹配"
    print(f"✓ 加密解密工具正常")
except Exception as e:
    print(f"✗ 工具类测试失败: {e}")
    sys.exit(1)
print()

# 测试4: API客户端
print(">>> 测试4: API客户端...")
try:
    from app.douyin_client import DouyinClient, DouyinAPIError
    print("✓ API客户端导入成功")
except Exception as e:
    print(f"✗ API客户端测试失败: {e}")
    sys.exit(1)
print()

# 测试5: Celery任务
print(">>> 测试5: Celery任务...")
try:
    from app.tasks.order_sync import OrderSyncTask
    from app.tasks.stats_sync import StatsSyncTask
    print("✓ Celery任务导入成功")
except Exception as e:
    print(f"✗ Celery任务测试失败: {e}")
    sys.exit(1)
print()

print("=" * 60)
print("✅ 所有测试通过!")
print("=" * 60)
print()
print("系统已就绪,可以启动同步服务:")
print("  ./manage.sh start")
