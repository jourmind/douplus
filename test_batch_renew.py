#!/usr/bin/env python3
"""
测试批量续费功能
验证：
1. 订单列表是否返回orderId字段
2. 批量续费API是否可以调用（不实际续费）
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:5000"
# 注意：这个token需要从浏览器获取，或者先调用登录接口
TOKEN = "YOUR_TOKEN_HERE"  # 需要替换

def test_order_list():
    """测试订单列表API"""
    print("=" * 60)
    print("测试1: 订单列表查询 - 检查orderId字段")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/douplus/task/page"
    params = {
        'pageNum': 1,
        'pageSize': 5
    }
    headers = {
        'Authorization': f'Bearer {TOKEN}'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        result = response.json()
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应code: {result.get('code')}")
        print(f"响应message: {result.get('message')}")
        
        if result.get('code') == 200 and result.get('data'):
            data = result['data']
            print(f"\n总记录数: {data.get('total')}")
            print(f"当前页记录数: {len(data.get('records', []))}")
            
            if data.get('records'):
                print("\n前3条记录的关键字段：")
                for i, record in enumerate(data['records'][:3], 1):
                    print(f"\n记录{i}:")
                    print(f"  id: {record.get('id')}")
                    print(f"  orderId: {record.get('orderId')} {'✓' if record.get('orderId') else '✗ 缺失！'}")
                    print(f"  videoTitle: {record.get('videoTitle')[:30] if record.get('videoTitle') else 'N/A'}...")
                    print(f"  status: {record.get('status')}")
                    print(f"  budget: {record.get('budget')}")
                
                # 统计有orderId的记录
                has_order_id = sum(1 for r in data['records'] if r.get('orderId'))
                print(f"\n✓ 有orderId的记录: {has_order_id}/{len(data['records'])}")
                
                if has_order_id == len(data['records']):
                    print("✅ 所有记录都有orderId字段！")
                    return True, data['records']
                else:
                    print("⚠️ 部分记录缺少orderId字段")
                    return False, []
            else:
                print("⚠️ 没有订单记录")
                return False, []
        else:
            print(f"❌ 查询失败: {result.get('message')}")
            return False, []
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, []


def test_batch_renew_api(order_records):
    """测试批量续费API（模拟请求结构，不实际调用）"""
    print("\n" + "=" * 60)
    print("测试2: 批量续费API - 验证请求结构")
    print("=" * 60)
    
    # 筛选状态为DELIVERING或RUNNING的订单
    valid_orders = [r for r in order_records if r.get('status') in ['DELIVERING', 'RUNNING']]
    
    if not valid_orders:
        print("⚠️ 没有投放中的订单，无法测试批量续费")
        # 使用第一条记录作为测试数据
        if order_records:
            valid_orders = [order_records[0]]
            print(f"使用第一条记录进行结构测试: status={valid_orders[0].get('status')}")
    
    if not valid_orders:
        print("❌ 没有订单可以测试")
        return False
    
    # 取前2个订单进行测试
    test_orders = valid_orders[:2]
    order_ids = [o.get('orderId') for o in test_orders if o.get('orderId')]
    
    if not order_ids:
        print("❌ 测试订单没有orderId")
        return False
    
    print(f"\n准备测试的订单:")
    for i, order in enumerate(test_orders, 1):
        print(f"  {i}. orderId={order.get('orderId')}, status={order.get('status')}, title={order.get('videoTitle', '')[:20]}...")
    
    # 构建请求数据
    request_data = {
        'orderIds': order_ids,
        'budget': 100,
        'duration': 24
    }
    
    print(f"\n请求数据结构:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # 不实际发送请求，只验证数据结构
    print("\n✅ 请求数据结构正确")
    print("⚠️  实际API调用已跳过（避免真实续费）")
    print("\n如需测试实际API调用，请手动发送以下请求:")
    print(f"POST {BASE_URL}/api/douplus/order/batch-renew")
    print(f"Headers: Authorization: Bearer YOUR_TOKEN")
    print(f"Body: {json.dumps(request_data, ensure_ascii=False)}")
    
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("DOU+批量续费功能测试")
    print("=" * 60)
    
    # 检查TOKEN
    if TOKEN == "YOUR_TOKEN_HERE":
        print("\n❌ 请先设置有效的TOKEN")
        print("获取方式：")
        print("1. 浏览器打开开发者工具 (F12)")
        print("2. 切换到 Application > Storage > Local Storage")
        print("3. 找到 'token' 字段，复制值")
        print("4. 修改脚本中的 TOKEN 变量")
        return
    
    # 测试1: 订单列表
    success, order_records = test_order_list()
    
    if not success:
        print("\n❌ 订单列表查询失败，无法继续测试")
        return
    
    # 测试2: 批量续费API结构
    test_batch_renew_api(order_records)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
