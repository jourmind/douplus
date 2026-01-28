#!/usr/bin/env python3
"""
测试订单导出API

测试场景：
1. 无筛选条件导出
2. 按状态筛选导出
3. 按账号筛选导出
4. 按时间范围筛选导出
"""

import requests
import os
from datetime import datetime, timedelta

# API配置
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
EXPORT_URL = f"{BASE_URL}/api/douplus/task/export"

# 测试账号（需要修改为实际账号）
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

def login():
    """登录获取token"""
    print("正在登录...")
    response = requests.post(LOGIN_URL, json=TEST_USER)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            # 尝试不同的token路径
            token = (data.get('data', {}).get('accessToken') or 
                    data.get('data', {}).get('token') or 
                    data.get('token'))
            if token:
                print(f"✓ 登录成功，token: {token[:20]}...")
                return token
    print(f"✗ 登录失败: {response.text}")
    return None

def test_export(token, params=None, filename_suffix=""):
    """测试导出功能"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n测试导出 {filename_suffix}...")
    print(f"  参数: {params or '无'}")
    
    response = requests.get(EXPORT_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        # 获取文件名
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            filename = f"订单数据{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 保存文件
        output_dir = "/opt/douplus/test_exports"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content)
        print(f"✓ 导出成功")
        print(f"  文件: {filepath}")
        print(f"  大小: {file_size:,} 字节")
        return True
    else:
        print(f"✗ 导出失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return False

def main():
    print("=" * 60)
    print("订单导出API测试")
    print("=" * 60)
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 测试各种导出场景
    tests = [
        {
            "name": "全量导出",
            "params": None,
            "suffix": "_全量"
        },
        {
            "name": "按状态筛选（投放中）",
            "params": {"status": "DELIVERING"},
            "suffix": "_投放中"
        },
        {
            "name": "按状态筛选（已完成）",
            "params": {"status": "DELIVERIED"},
            "suffix": "_已完成"
        },
        {
            "name": "按关键词筛选",
            "params": {"keyword": "测试"},
            "suffix": "_关键词"
        },
        {
            "name": "按时间范围筛选（最近7天）",
            "params": {
                "startDate": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                "endDate": datetime.now().strftime('%Y-%m-%d')
            },
            "suffix": "_最近7天"
        }
    ]
    
    success_count = 0
    for test in tests:
        if test_export(token, test["params"], test["suffix"]):
            success_count += 1
    
    # 汇总结果
    print("\n" + "=" * 60)
    print(f"测试完成: {success_count}/{len(tests)} 个测试通过")
    print("=" * 60)

if __name__ == '__main__':
    main()
