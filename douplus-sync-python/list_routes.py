#!/usr/bin/env python3
"""列出Flask应用的所有路由"""

import sys
from api_server import app

def list_routes():
    """列出所有路由"""
    print("=" * 80)
    print("Flask 应用所有路由")
    print("=" * 80)
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': str(rule)
        })
    
    # 按路径排序
    routes.sort(key=lambda x: x['path'])
    
    # 打印路由
    for route in routes:
        print(f"{route['methods']:10s} {route['path']:50s} -> {route['endpoint']}")
    
    print("=" * 80)
    print(f"总共 {len(routes)} 个路由")
    print("=" * 80)

if __name__ == '__main__':
    list_routes()
