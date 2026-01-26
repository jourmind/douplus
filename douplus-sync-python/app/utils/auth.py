"""
认证工具：JWT和密码处理
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from app.config import get_settings

settings = get_settings()

# JWT配置
JWT_SECRET = "douplus-jwt-secret-key-default"  # 应该从环境变量读取
JWT_EXPIRATION = 86400  # 24小时


def hash_password(password: str) -> str:
    """
    密码哈希
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False


def generate_token(user_id: int, username: str) -> str:
    """
    生成JWT token
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


def decode_token(token: str) -> dict:
    """
    解码JWT token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """
    认证装饰器
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'code': 1001,
                'message': '未登录或token已过期',
                'success': False
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        
        if not payload:
            return jsonify({
                'code': 1001,
                'message': '未登录或token已过期',
                'success': False
            }), 401
        
        # 将用户信息添加到request context
        request.user_id = payload['user_id']
        request.username = payload['username']
        
        return f(*args, **kwargs)
    
    return decorated
