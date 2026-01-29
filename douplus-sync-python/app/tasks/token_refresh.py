"""
Token自动刷新任务

功能：
1. 定期检查即将过期的access_token（7天内）
2. 自动调用抖音API刷新token
3. 更新数据库中的token信息
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from sqlalchemy import text
from app.models import SessionLocal
from app.utils.crypto import encrypt_access_token
from app.config import get_settings

logger = logging.getLogger(__name__)


def refresh_expiring_tokens():
    """
    刷新即将过期的Token
    
    检查条件：
    - token_expires_at < now() + 7天
    - refresh_token存在
    - 账号未删除
    """
    db = SessionLocal()
    refreshed_count = 0
    failed_count = 0
    
    try:
        # 查询即将过期的账号（7天内）
        query_sql = text("""
            SELECT id, open_id, nickname, refresh_token, token_expires_at
            FROM douyin_account
            WHERE deleted = 0 
            AND refresh_token IS NOT NULL 
            AND refresh_token != ''
            AND token_expires_at < DATE_ADD(NOW(), INTERVAL 7 DAY)
            ORDER BY token_expires_at ASC
        """)
        
        accounts = db.execute(query_sql).fetchall()
        
        if not accounts:
            logger.info("没有需要刷新的Token")
            return {'refreshed': 0, 'failed': 0, 'message': '没有需要刷新的Token'}
        
        logger.info(f"发现 {len(accounts)} 个账号的Token需要刷新")
        
        # 获取配置
        settings = get_settings()
        app_id = settings.DOUPLUS_APP_ID
        app_secret = settings.DOUPLUS_APP_SECRET
        
        if not app_id or not app_secret:
            logger.error("缺少DOUPLUS_APP_ID或DOUPLUS_APP_SECRET配置")
            return {'refreshed': 0, 'failed': len(accounts), 'message': '系统配置错误'}
        
        # 遍历刷新
        for account in accounts:
            account_id, open_id, nickname, refresh_token, expires_at = account
            
            try:
                logger.info(f"开始刷新Token: account_id={account_id}, nickname={nickname}, expires_at={expires_at}")
                
                # 调用抖音API刷新token
                refresh_url = 'https://ad.oceanengine.com/open_api/oauth2/refresh_token/'
                payload = {
                    'app_id': app_id,
                    'secret': app_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token
                }
                
                response = requests.post(refresh_url, json=payload, timeout=30)
                result = response.json()
                
                if result.get('code') != 0 or 'data' not in result:
                    error_msg = result.get('message', '未知错误')
                    logger.error(f"刷新Token失败: account_id={account_id}, error={error_msg}")
                    failed_count += 1
                    continue
                
                # 获取新token
                token_data = result['data']
                new_access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 86400)  # 默认1天
                
                if not new_access_token:
                    logger.error(f"刷新Token失败: account_id={account_id}, 未返回access_token")
                    failed_count += 1
                    continue
                
                # 加密新token
                encrypted_token = encrypt_access_token(new_access_token)
                new_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # 更新数据库
                update_sql = text("""
                    UPDATE douyin_account
                    SET access_token_encrypted = :access_token,
                        refresh_token = :refresh_token,
                        token_expires_at = :expires_at,
                        update_time = NOW()
                    WHERE id = :account_id
                """)
                
                db.execute(update_sql, {
                    'access_token': encrypted_token,
                    'refresh_token': new_refresh_token or refresh_token,
                    'expires_at': new_expires_at,
                    'account_id': account_id
                })
                db.commit()
                
                refreshed_count += 1
                logger.info(f"Token刷新成功: account_id={account_id}, new_expires_at={new_expires_at}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Token刷新网络错误: account_id={account_id}, error={str(e)}")
                failed_count += 1
                db.rollback()
            except Exception as e:
                logger.error(f"Token刷新失败: account_id={account_id}, error={str(e)}")
                failed_count += 1
                db.rollback()
        
        result = {
            'refreshed': refreshed_count,
            'failed': failed_count,
            'total': len(accounts),
            'message': f'Token刷新完成: 成功{refreshed_count}个, 失败{failed_count}个'
        }
        
        logger.info(result['message'])
        return result
        
    except Exception as e:
        logger.error(f"Token刷新任务执行失败: {str(e)}")
        return {'refreshed': 0, 'failed': 0, 'message': f'任务执行失败: {str(e)}'}
    finally:
        db.close()


def refresh_single_account_token(account_id: int):
    """
    刷新单个账号的Token
    
    Args:
        account_id: 账号ID
    
    Returns:
        dict: 刷新结果
    """
    db = SessionLocal()
    
    try:
        # 查询账号信息
        query_sql = text("""
            SELECT id, open_id, nickname, refresh_token, token_expires_at
            FROM douyin_account
            WHERE id = :account_id AND deleted = 0
        """)
        
        account = db.execute(query_sql, {'account_id': account_id}).fetchone()
        
        if not account:
            return {'success': False, 'message': '账号不存在'}
        
        account_id, open_id, nickname, refresh_token, expires_at = account
        
        if not refresh_token:
            return {'success': False, 'message': '该账号没有refresh_token'}
        
        # 获取配置
        settings = get_settings()
        app_id = settings.DOUPLUS_APP_ID
        app_secret = settings.DOUPLUS_APP_SECRET
        
        if not app_id or not app_secret:
            return {'success': False, 'message': '系统配置错误'}
        
        # 调用抖音API
        refresh_url = 'https://ad.oceanengine.com/open_api/oauth2/refresh_token/'
        payload = {
            'app_id': app_id,
            'secret': app_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(refresh_url, json=payload, timeout=30)
        result = response.json()
        
        if result.get('code') != 0 or 'data' not in result:
            error_msg = result.get('message', '刷新Token失败')
            return {'success': False, 'message': error_msg}
        
        # 获取新token
        token_data = result['data']
        new_access_token = token_data.get('access_token')
        new_refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 86400)
        
        if not new_access_token:
            return {'success': False, 'message': '未返回新的access_token'}
        
        # 加密并更新
        encrypted_token = encrypt_access_token(new_access_token)
        new_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        update_sql = text("""
            UPDATE douyin_account
            SET access_token_encrypted = :access_token,
                refresh_token = :refresh_token,
                token_expires_at = :expires_at,
                update_time = NOW()
            WHERE id = :account_id
        """)
        
        db.execute(update_sql, {
            'access_token': encrypted_token,
            'refresh_token': new_refresh_token or refresh_token,
            'expires_at': new_expires_at,
            'account_id': account_id
        })
        db.commit()
        
        logger.info(f"Token刷新成功: account_id={account_id}, expires_at={new_expires_at}")
        
        return {
            'success': True,
            'message': 'Token刷新成功',
            'tokenExpiresAt': new_expires_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"刷新Token失败: account_id={account_id}, error={str(e)}")
        return {'success': False, 'message': str(e)}
    finally:
        db.close()
