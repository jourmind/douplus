#!/usr/bin/env python3
"""
验证前端导出API调用

模拟前端fetch调用，检查：
1. API路径是否正确
2. Token认证是否正常
3. 响应内容类型
4. 文件下载头部
"""

import requests
import json

# API配置
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
EXPORT_URL = f"{BASE_URL}/api/douplus/task/export"

# 测试账号
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

def test_frontend_export():
    """模拟前端导出调用"""
    
    print("=" * 60)
    print("前端导出API调用验证")
    print("=" * 60)
    
    # 1. 登录
    print("\n1. 登录获取token...")
    response = requests.post(LOGIN_URL, json=TEST_USER)
    if response.status_code != 200:
        print(f"✗ 登录失败: {response.status_code}")
        return
    
    data = response.json()
    if data.get('code') != 200:
        print(f"✗ 登录失败: {data}")
        return
    
    token = data['data']['accessToken']
    print(f"✓ 登录成功")
    print(f"  Token: {token[:30]}...")
    
    # 2. 测试导出API（模拟前端fetch调用）
    print("\n2. 测试导出API...")
    
    # 构建URL（与前端完全一致）
    params = {}  # 无筛选条件
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    url = f"{EXPORT_URL}?{query_string}" if query_string else EXPORT_URL
    
    print(f"  请求URL: {url}")
    print(f"  请求方法: GET")
    print(f"  Authorization: Bearer {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(url, headers=headers, stream=True)
    
    print(f"\n3. 响应结果:")
    print(f"  状态码: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type')}")
    print(f"  Content-Disposition: {response.headers.get('Content-Disposition')}")
    
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if 'spreadsheetml' in content_type or 'excel' in content_type:
            print(f"✓ 导出成功！")
            print(f"  文件大小: {len(response.content):,} 字节")
            
            # 保存文件验证
            test_file = "/tmp/test_export_from_frontend.xlsx"
            with open(test_file, 'wb') as f:
                f.write(response.content)
            print(f"  测试文件: {test_file}")
        else:
            print(f"✗ 响应类型错误")
            print(f"  响应内容: {response.text[:200]}")
    else:
        print(f"✗ 导出失败")
        print(f"  响应内容: {response.text[:500]}")
    
    # 4. 测试带筛选条件的导出
    print("\n4. 测试带筛选条件的导出...")
    params = {
        'status': 'DELIVERING'
    }
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    url = f"{EXPORT_URL}?{query_string}"
    
    print(f"  请求URL: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"✓ 筛选导出成功！文件大小: {len(response.content):,} 字节")
    else:
        print(f"✗ 筛选导出失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

if __name__ == '__main__':
    test_frontend_export()
