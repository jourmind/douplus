#!/usr/bin/env python3
"""对比两个页面获取账号列表的行为"""

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
print("模拟前端请求 - 账号列表API")
print("=" * 80)

# 请求API
response = requests.get(
    'https://127.0.0.1/api/account/list',
    headers={'Authorization': f'Bearer {token}'},
    verify=False
)

data = response.json()

print(f"\nHTTP状态码: {response.status_code}")
print(f"业务code: {data.get('code')}")
print(f"success: {data.get('success')}")
print(f"data类型: {type(data.get('data'))}")
print(f"data是否为None: {data.get('data') is None}")
print(f"data是否为空列表: {data.get('data') == []}")
print(f"账号数量: {len(data.get('data', []))}")

# 模拟首页概览的处理
print("\n" + "=" * 80)
print("首页概览的处理逻辑:")
print("=" * 80)
if data.get('code') == 200 and data.get('data'):
    accountList = data.get('data')
    print(f"✅ 条件通过: code={data.get('code')}, data存在")
    print(f"accountList长度: {len(accountList)}")
    for acc in accountList:
        print(f"  - ID: {acc.get('id')}, Nickname: {acc.get('nickname')}")
else:
    print(f"❌ 条件不通过: code={data.get('code')}, data={data.get('data')}")

# 模拟投放记录的处理
print("\n" + "=" * 80)
print("投放记录的处理逻辑:")
print("=" * 80)
if data.get('code') == 200:
    print(f"✅ 条件通过: code={data.get('code')}")
    members = [(acc.get('remark') or acc.get('nickname') or f"账号{acc.get('id')}")
               for acc in (data.get('data') or [])]
    print(f"members数组长度: {len(members)}")
    for i, member in enumerate(members):
        acc = data.get('data', [])[i] if data.get('data') else None
        if acc:
            print(f"  - ID: {acc.get('id')}, Nickname: {member}")
else:
    print(f"❌ 条件不通过: code={data.get('code')}")

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
if data.get('code') == 200 and data.get('data'):
    print("✅ 两个页面的逻辑应该都能正常工作")
else:
    print("❌ 存在问题，需要排查")
