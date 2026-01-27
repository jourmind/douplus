"""
账号管理API

职责：
1. 账号列表查询
2. 账号详情查询
3. 账号创建/更新/删除
4. OAuth授权URL生成

架构原则：
- 纯CRUD操作
- 不涉及业务逻辑
"""

import logging
import os
from datetime import datetime, timedelta
from flask import request
from sqlalchemy import text
from app.api import account_bp
from app.api.common import require_auth, success_response, error_response
from app.models import SessionLocal

logger = logging.getLogger(__name__)


@account_bp.route('/accounts', methods=['GET'])
@account_bp.route('/account/list', methods=['GET'])  # 前端兼容路由
@require_auth
def get_accounts():
    """
    获取账号列表
    
    返回用户所有账号的基本信息
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        query_sql = """
            SELECT 
                id, open_id, advertiser_id, nickname, avatar, 
                fans_count, following_count, total_favorited, 
                status, daily_limit, balance, remark, 
                token_expires_at, create_time
            FROM douyin_account
            WHERE user_id = :user_id AND deleted = 0
            ORDER BY create_time DESC
        """
        
        results = db.execute(text(query_sql), {'user_id': user_id}).fetchall()
        
        accounts = []
        for row in results:
            # 判断Token是否即将过期（7天内）
            token_expiring_soon = False
            if row[12]:  # token_expires_at
                if isinstance(row[12], str):
                    expires_at = datetime.fromisoformat(row[12])
                else:
                    expires_at = row[12]
                token_expiring_soon = expires_at < datetime.now() + timedelta(days=7)
            
            account = {
                'id': row[0],
                'openId': row[1],
                'advertiserId': row[2],
                'douyinId': row[1],
                'nickname': row[3],
                'avatar': row[4],
                'fansCount': row[5] or 0,
                'followingCount': row[6] or 0,
                'totalFavorited': row[7] or 0,
                'status': row[8],
                'dailyLimit': float(row[9]) if row[9] else 0,
                'balance': float(row[10]) if row[10] else 0,
                'couponCount': 0,
                'remark': row[11],
                'companyName': None,
                'tokenExpiresAt': row[12].isoformat() if row[12] else None,
                'createTime': row[13].isoformat() if row[13] else None,
                'tokenExpiringSoon': token_expiring_soon
            }
            accounts.append(account)
        
        return success_response(accounts)
        
    except Exception as e:
        logger.error(f"查询账号列表失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@account_bp.route('/account/<int:account_id>', methods=['GET'])
@require_auth
def get_account_by_id(account_id):
    """
    获取指定账号的详细信息
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        query_sql = text("""
            SELECT 
                id, open_id, advertiser_id, nickname, avatar, 
                fans_count, following_count, total_favorited, 
                status, daily_limit, balance, remark, 
                token_expires_at, create_time
            FROM douyin_account
            WHERE id = :account_id AND user_id = :user_id AND deleted = 0
        """)
        
        row = db.execute(query_sql, {
            'account_id': account_id,
            'user_id': user_id
        }).fetchone()
        
        if not row:
            return error_response('账号不存在', code=404)
        
        # 判断Token是否即将过期
        token_expiring_soon = False
        if row[12]:
            if isinstance(row[12], str):
                expires_at = datetime.fromisoformat(row[12])
            else:
                expires_at = row[12]
            token_expiring_soon = expires_at < datetime.now() + timedelta(days=7)
        
        account = {
            'id': row[0],
            'openId': row[1],
            'advertiserId': row[2],
            'douyinId': row[1],
            'nickname': row[3],
            'avatar': row[4],
            'fansCount': row[5] or 0,
            'followingCount': row[6] or 0,
            'totalFavorited': row[7] or 0,
            'status': row[8],
            'dailyLimit': float(row[9]) if row[9] else 0,
            'balance': float(row[10]) if row[10] else 0,
            'couponCount': 0,
            'remark': row[11],
            'companyName': None,
            'tokenExpiresAt': row[12].isoformat() if row[12] else None,
            'createTime': row[13].isoformat() if row[13] else None,
            'tokenExpiringSoon': token_expiring_soon
        }
        
        return success_response(account)
        
    except Exception as e:
        logger.error(f"查询账号失败: {str(e)}")
        return error_response(str(e))
    finally:
        db.close()


@account_bp.route('/account/oauth/url', methods=['GET'])
@require_auth
def get_oauth_url():
    """
    获取抖音OAuth授权URL
    
    返回抖音开放平台的授权页面URL
    """
    try:
        # 从环境变量获取配置
        app_id = os.getenv('DOUPLUS_APP_ID')
        callback_url = os.getenv('DOUPLUS_CALLBACK_URL', 'https://42.194.181.242/oauth/douplus.php')
        
        if not app_id:
            return error_response('OAuth配置缺失：未配置DOUPLUS_APP_ID', code=500)
        
        # 使用官方提供的授权URL格式（巨量引擎）
        # 注意：使用open.oceanengine.com而不是open.douyin.com
        oauth_url = f"https://open.oceanengine.com/audit/oauth.html?app_id={app_id}&state=douplus&material_auth=1"
        
        return success_response(oauth_url)
        
    except Exception as e:
        logger.error(f"获取OAuth URL失败: {str(e)}")
        return error_response(f'获取授权链接失败：{str(e)}', code=500)


@account_bp.route('/account/<int:account_id>', methods=['DELETE'])
@require_auth
def delete_account(account_id):
    """
    删除（解绑）账号
    
    将账号标记为已删除（软删除）
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 检查账号是否存在且属于当前用户
        check_sql = text("""
            SELECT id FROM douyin_account
            WHERE id = :account_id AND user_id = :user_id AND deleted = 0
        """)
        
        account = db.execute(check_sql, {
            'account_id': account_id,
            'user_id': user_id
        }).fetchone()
        
        if not account:
            return error_response('账号不存在或无权操作', code=404)
        
        # 软删除账号
        delete_sql = text("""
            UPDATE douyin_account
            SET deleted = 1, update_time = NOW()
            WHERE id = :account_id AND user_id = :user_id
        """)
        
        db.execute(delete_sql, {
            'account_id': account_id,
            'user_id': user_id
        })
        db.commit()
        
        logger.info(f"账号已删除: account_id={account_id}, user_id={user_id}")
        return success_response(None, message='账号已解绑')
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除账号失败: {str(e)}")
        return error_response(f'删除账号失败：{str(e)}', code=500)
    finally:
        db.close()


@account_bp.route('/account/<int:account_id>/refresh-token', methods=['POST'])
@require_auth
def refresh_account_token(account_id):
    """
    刷新账号的access_token
    
    使用refresh_token换取新的access_token
    """
    user_id = request.user_id
    
    db = SessionLocal()
    try:
        # 查询账号信息
        query_sql = text("""
            SELECT id, refresh_token, access_token_encrypted
            FROM douyin_account
            WHERE id = :account_id AND user_id = :user_id AND deleted = 0
        """)
        
        account = db.execute(query_sql, {
            'account_id': account_id,
            'user_id': user_id
        }).fetchone()
        
        if not account:
            return error_response('账号不存在或无权操作', code=404)
        
        refresh_token = account[1]
        if not refresh_token:
            return error_response('该账号没有refresh_token，请重新授权', code=400)
        
        # 调用抖音API刷新token
        # 注意：这里需要实现抖音的refresh_token接口调用
        # 参考文档：https://ad.oceanengine.com/openapi/doc/index.html?id=596
        app_id = os.getenv('DOUPLUS_APP_ID')
        app_secret = os.getenv('DOUPLUS_APP_SECRET')
        
        if not app_id or not app_secret:
            return error_response('系统配置错误：缺少APP_ID或APP_SECRET', code=500)
        
        # 构建刷新token的请求
        import requests
        refresh_url = 'https://ad.oceanengine.com/open_api/oauth2/refresh_token/'
        
        payload = {
            'app_id': app_id,
            'secret': app_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        logger.info(f"刷新Token请求: account_id={account_id}")
        
        response = requests.post(refresh_url, json=payload, timeout=30)
        result = response.json()
        
        logger.info(f"刷新Token响应: {result}")
        
        if result.get('code') != 0 or 'data' not in result:
            error_msg = result.get('message', '刷新Token失败')
            return error_response(f'刷新Token失败：{error_msg}', code=500)
        
        token_data = result['data']
        new_access_token = token_data.get('access_token')
        new_refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 86400)  # 默认1天
        
        if not new_access_token:
            return error_response('刷新Token失败：未返回新的access_token', code=500)
        
        # 加密新的access_token
        from app.utils.crypto import encrypt_access_token
        encrypted_token = encrypt_access_token(new_access_token)
        
        # 计算过期时间
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # 更新数据库
        update_sql = text("""
            UPDATE douyin_account
            SET access_token_encrypted = :access_token,
                refresh_token = :refresh_token,
                token_expires_at = :expires_at,
                update_time = NOW()
            WHERE id = :account_id AND user_id = :user_id
        """)
        
        db.execute(update_sql, {
            'access_token': encrypted_token,
            'refresh_token': new_refresh_token or refresh_token,  # 如果没返回新的就用旧的
            'expires_at': expires_at,
            'account_id': account_id,
            'user_id': user_id
        })
        db.commit()
        
        logger.info(f"Token刷新成功: account_id={account_id}, expires_at={expires_at}")
        
        return success_response({
            'tokenExpiresAt': expires_at.isoformat(),
            'message': 'Token刷新成功'
        })
        
    except requests.exceptions.RequestException as e:
        db.rollback()
        logger.error(f"刷新Token网络请求失败: {str(e)}")
        return error_response(f'网络请求失败：{str(e)}', code=500)
    except Exception as e:
        db.rollback()
        logger.error(f"刷新Token失败: {str(e)}")
        return error_response(f'刷新Token失败：{str(e)}', code=500)
    finally:
        db.close()
