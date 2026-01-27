#!/usr/bin/env python3
"""
直接查看API原始响应
"""
from app.models import SessionLocal, DouyinAccount
from app.utils.crypto import decrypt_access_token
import httpx
import json
from datetime import datetime, timedelta

db = SessionLocal()

try:
    account = db.query(DouyinAccount).filter_by(deleted=0).first()
    access_token = decrypt_access_token(account.access_token)
    
    # 构建请求
    url = "https://api.oceanengine.com/open_api/v3.0/douplus/order/report/"
    
    begin_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_time = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        "aweme_sec_uid": account.aweme_sec_uid,
        "stat_time": json.dumps({
            "begin_time": begin_time,
            "end_time": end_time
        }),
        "group_by": json.dumps(["GROUP_BY_AD_ID"])
    }
    
    headers = {
        "Access-Token": access_token
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数:")
    for k, v in params.items():
        print(f"  {k}: {v}")
    print()
    
    # 发送请求
    client = httpx.Client(timeout=30.0)
    try:
        response = client.get(url, params=params, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    finally:
        client.close()
        
finally:
    db.close()
