#!/usr/bin/env python3
"""直接查看account/list API返回的原始数据"""

import jwt
import requests
import json
from datetime import datetime, timedelta

# 生成有效token
token = jwt.encode({
    'user_id': 1,
    'username': 'test@test.com',
    'exp': int((datetime.utcnow() + timedelta(days=30)).timestamp())
}, 'douplus-jwt-secret-key-default', algorithm='HS256')

print("=" * 80)
print("获取账号列表API原始数据")
print("=" * 80)

# 请求API
response = requests.get(
    'https://127.0.0.1/api/account/list',
    headers={'Authorization': f'Bearer {token}'},
    verify=False
)

data = response.json()

print(f"\n状态码: {response.status_code}")
print(f"code: {data.get('code')}")
print(f"success: {data.get('success')}")
print(f"账号数量: {len(data.get('data', []))}")
print("\n" + "=" * 80)
print("原始返回数据:")
print("=" * 80)
print(json.dumps(data, ensure_ascii=False, indent=2))

print("\n" + "=" * 80)
print("前端需要的格式 (members数组):")
print("=" * 80)

members = []
for account in data.get('data', []):
    member = {
        'id': account.get('id'),
        'nickname': account.get('remark') or account.get('nickname') or f"账号{account.get('id')}"
    }
    members.append(member)
    print(f"  - ID: {member['id']}, Nickname: {member['nickname']}")

print(f"\nmembers.length = {len(members)}")
print(f"members数组: {json.dumps(members, ensure_ascii=False)}")
