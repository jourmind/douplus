#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/douplus/douplus-sync-python')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 查询这个订单的详细信息
result = db.execute(text('''
    SELECT o.order_id, o.item_id, o.status, a.aweme_sec_uid, a.open_id
    FROM douplus_order o
    JOIN douyin_account a ON o.account_id = a.id
    WHERE o.order_id = '1855431230726176'
    LIMIT 1
''')).fetchone()

if result:
    print(f'订单ID: {result[0]}')
    print(f'视频ID(item_id): {result[1]}')
    print(f'订单状态: {result[2]}')
    print(f'账号aweme_sec_uid: {result[3]}')
    print(f'账号open_id: {result[4]}')
else:
    print('订单不存在')

db.close()
