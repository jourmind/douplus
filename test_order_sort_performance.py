"""
测试订单预聚合表查询性能和排序功能
"""

import requests
import time

BASE_URL = 'http://localhost:5000/api/douplus'

# 从之前的测试获取token
token = open('/tmp/test_token_temp.txt').read().strip() if os.path.exists('/tmp/test_token_temp.txt') else None

headers = {}
if token:
    headers['Authorization'] = f'Bearer {token}'

def test_sort_performance(sort_field='playCount', sort_order='desc'):
    """测试排序查询性能"""
    print(f"\n{'='*80}")
    print(f"测试排序: {sort_field} {sort_order}")
    print(f"{'='*80}")
    
    params = {
        'pageNum': 1,
        'pageSize': 20,
        'sortField': sort_field,
        'sortOrder': sort_order,
        'accountId': 5,
        'startDate': '2025-12-30',
        'endDate': '2026-01-28'
    }
    
    start_time = time.time()
    response = requests.get(f'{BASE_URL}/task/page', params=params, headers=headers)
    elapsed = time.time() - start_time
    
    print(f"响应时间: {elapsed:.3f}秒")
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            records = data['data']['records']
            print(f"返回记录数: {len(records)}")
            print(f"\n前5条记录:")
            print(f"{'订单ID':<20} {'消耗':>10} {'播放量':>10} {'转化成本':>12}")
            print('-' * 55)
            for i, record in enumerate(records[:5]):
                stats = record.get('stats', {})
                print(f"{record['orderId']:<20} "
                      f"{stats.get('actualCost', 0):>10.2f} "
                      f"{stats.get('playCount', 0):>10} "
                      f"{stats.get('customConvertCost', '-'):>12}")
        else:
            print(f"错误: {data.get('message')}")
    else:
        print(f"HTTP错误: {response.status_code}")
        print(response.text)

import os

if __name__ == '__main__':
    # 测试不同的排序字段
    test_sort_performance('playCount', 'desc')  # 百播放量降序
    test_sort_performance('actualCost', 'desc')  # 消耗降序
    test_sort_performance('costPerPlay', 'asc')  # 转化成本升序
    test_sort_performance('createTime', 'desc')  # 创建时间降序
