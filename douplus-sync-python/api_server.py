"""
DOU+订单管理系统 - API服务器（模块化架构）

三层解耦架构：
1. 同步层 (sync_api) - 订单采集、历史同步
2. 统计层 (stats_api) - 数据聚合、统计计算
3. 查询层 (query_api) - 前端查询、数据展示
4. 账号管理 (account_api) - 账号CRUD操作

代码组织：
- app/api/sync_api.py - 同步层接口
- app/api/stats_api.py - 统计层接口
- app/api/query_api.py - 查询层接口
- app/api/account_api.py - 账号管理接口
- app/api/common.py - 通用工具（认证、响应）
"""

import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 启用CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 注册API蓝图（模块化）
from app.api import register_blueprints
register_blueprints(app)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'douplus-api',
        'version': '2.0.0',
        'architecture': 'three-tier-decoupled'
    })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'code': 404,
        'message': 'API接口不存在',
        'success': False
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器内部错误: {str(error)}")
    return jsonify({
        'code': 500,
        'message': '服务器内部错误',
        'success': False
    }), 500


if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("="*60)
    logger.info("DOU+订单管理系统 API服务器启动")
    logger.info("三层解耦架构：同步层 → 统计层 → 查询层")
    logger.info("="*60)
    
    # 启动Flask服务
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
