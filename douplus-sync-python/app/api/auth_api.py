"""
认证API模块
处理用户登录、用户信息查询等认证相关接口
"""

import jwt
import logging
from datetime import datetime, timedelta
from flask import request, jsonify
from sqlalchemy import text
from app.models import SessionLocal
from . import auth_bp

logger = logging.getLogger(__name__)

# JWT配置（与common.py保持一致）
JWT_SECRET = 'douplus-jwt-secret-key-default'
JWT_ALGORITHM = 'HS256'


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    
    请求体:
    {
        "username": "admin",
        "password": "admin123"
    }
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "accessToken": "jwt_token_string",
            "tokenType": "Bearer",
            "expiresIn": 86400000,
            "user": {
                "id": 1,
                "username": "admin"
            }
        },
        "success": true
    }
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名或密码不能为空',
                'success': False
            }), 400
        
        # TODO: 实际应该查询数据库验证用户名密码
        # 目前简化处理：只要提供了用户名密码就登录成功
        # 生产环境需要：
        # 1. 查询用户表验证用户名密码
        # 2. 密码使用bcrypt等加密算法验证
        # 3. 记录登录日志
        
        # 生成JWT token
        payload = {
            'user_id': 1,
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=1000),  # 1000天有效期
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'accessToken': token,
                'tokenType': 'Bearer',
                'expiresIn': 86400000,  # 1000天的毫秒数
                'user': {
                    'id': 1,
                    'username': username
                }
            },
            'success': True
        })
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}',
            'success': False
        }), 500


@auth_bp.route('/info', methods=['GET'])
def get_user_info():
    """
    获取当前登录用户信息
    
    请求头:
    Authorization: Bearer jwt_token
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "username": "admin"
        },
        "success": true
    }
    """
    try:
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证信息',
                'success': False
            }), 401
        
        # 解析token
        try:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
            
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id')
            username = payload.get('username')
            
            if not user_id:
                return jsonify({
                    'code': 401,
                    'message': 'Token无效',
                    'success': False
                }), 401
            
            # 返回用户信息
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'id': user_id,
                    'username': username
                },
                'success': True
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'message': 'Token已过期',
                'success': False
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'message': 'Token无效',
                'success': False
            }), 401
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取用户信息失败: {str(e)}',
            'success': False
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出
    
    注意：JWT是无状态的，前端只需删除本地token即可
    """
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': None,
        'success': True
    })
