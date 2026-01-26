"""
API通用工具和装饰器
"""

from functools import wraps
from flask import request, jsonify
import jwt
import logging

logger = logging.getLogger(__name__)

# JWT配置（与utils/auth.py保持一致）
JWT_SECRET = 'douplus-jwt-secret-key-default'
JWT_ALGORITHM = 'HS256'


def require_auth(f):
    """
    JWT认证装饰器
    
    从Authorization头获取token并解析user_id
    将user_id注入到request对象中
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证信息',
                'success': False
            }), 401
        
        try:
            # Bearer token格式
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
            
            # 解析JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user_id = payload.get('user_id')
            request.username = payload.get('username')
            
            if not request.user_id:
                return jsonify({
                    'code': 401,
                    'message': 'Token无效',
                    'success': False
                }), 401
            
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
            logger.error(f"认证失败: {str(e)}")
            return jsonify({
                'code': 401,
                'message': '认证失败',
                'success': False
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def success_response(data=None, message='success'):
    """成功响应"""
    return jsonify({
        'code': 200,
        'message': message,
        'data': data,
        'success': True
    })


def error_response(message, code=500, data=None):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'success': False
    }), code


def paginated_response(records, total, page_num, page_size):
    """分页响应"""
    return success_response({
        'records': records,
        'total': total,
        'pageNum': page_num,
        'pageSize': page_size,
        'pages': (total + page_size - 1) // page_size if page_size > 0 else 0
    })
