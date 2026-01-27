#!/usr/bin/env python3
"""生成有效的JWT token并测试账号列表API"""

import sys
import jwt
from datetime import datetime, timedelta
import requests
import json

# JWT配置
SECRET_KEY = "douplus-jwt-secret-key-default"

# 生成token
user_id = 1
email = "test@test.com"
exp = datetime.utcnow() + timedelta(days=30)

payload = {
    'user_id': user_id,  # 注意：使用下划线命名，不是驼峰
    'username': email,
    'exp': int(exp.timestamp())
}

token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

print("=" * 60)
print("生成新的JWT Token")
print("=" * 60)
print(f"Token: {token}")
print(f"过期时间: {exp}")
print()

# 测试API
print("=" * 60)
print("测试账号列表API")
print("=" * 60)

headers = {
    'Authorization': f'Bearer {token}'
}

# 测试1: /api/account/list
print("\n1. GET https://127.0.0.1/api/account/list")
try:
    response = requests.get(
        'https://127.0.0.1/api/account/list',
        headers=headers,
        verify=False,
        timeout=5
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    if data.get('success'):
        print(f"\n✅ 成功！返回 {len(data.get('data', []))} 个账号")
        for account in data.get('data', [])[:3]:
            print(f"  - {account.get('nickname')} (ID: {account.get('id')})")
    else:
        print(f"\n❌ 失败: {data.get('message')}")
except Exception as e:
    print(f"❌ 请求失败: {str(e)}")

# 测试2: 直接访问5000端口
print("\n" + "=" * 60)
print("2. GET http://127.0.0.1:5000/api/account/list")
try:
    response = requests.get(
        'http://127.0.0.1:5000/api/account/list',
        headers=headers,
        timeout=5
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    if data.get('success'):
        print(f"\n✅ 成功！返回 {len(data.get('data', []))} 个账号")
    else:
        print(f"\n❌ 失败: {data.get('message')}")
except Exception as e:
    print(f"❌ 请求失败: {str(e)}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
