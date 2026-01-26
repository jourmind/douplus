"""
账号管理API

职责：
1. 账号列表查询
2. 账号详情查询
3. 账号创建/更新/删除

架构原则：
- 纯CRUD操作
- 不涉及业务逻辑
"""

import logging
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
