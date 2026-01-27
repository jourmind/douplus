"""
订单操作API - 订单续费、取消等操作

职责：
1. 订单续费（追加预算和时长）
2. 订单取消（未来扩展）
3. 投放密码验证

架构原则：
- 调用抖音DOU+开放平台API
- 验证用户权限和投放密码
- 记录操作日志
"""

import logging
from flask import request
from sqlalchemy import text
from app.api import order_bp
from app.api.common import require_auth, success_response, error_response
from app.models import SessionLocal
from app.douyin_client import DouyinClient, DouyinAPIError
from app.utils.crypto import decrypt_access_token

logger = logging.getLogger(__name__)


@order_bp.route('/task/renew', methods=['POST'])
@require_auth
def renew_order():
    """
    续费DOU+订单（追加预算和时长）
    
    请求参数：
    - orderId: 订单内部ID
    - budget: 追加预算（元）
    - duration: 延长时长（小时）
    - investPassword: 投放密码
    
    业务规则：
    - 不可以仅增加投放时长（budget必须>0）
    - 可以仅增加投放预算（duration可以为0）
    """
    user_id = request.user_id
    data = request.json
    
    order_id = data.get('orderId')
    budget = float(data.get('budget', 0))  # 元
    duration = float(data.get('duration', 0))  # 小时
    invest_password = data.get('investPassword')
    
    logger.info(f"收到续费请求: user_id={user_id}, order_id={order_id}, budget={budget}, duration={duration}")
    
    # 参数验证
    if not order_id:
        return error_response('订单ID不能为空', code=400)
    
    if not invest_password:
        return error_response('投放密码不能为空', code=400)
    
    # 业务规则验证：不可以仅增加时长
    if budget <= 0 and duration > 0:
        return error_response('不可以仅增加投放时长，请同时追加预算', code=400)
    
    if budget <= 0:
        return error_response('追加预算必须大于0', code=400)
    
    # 预算范围验证（100元-5000元，10的倍数）
    if budget < 100 or budget > 5000:
        return error_response('追加预算范围：100-5000元', code=400)
    
    if int(budget) % 10 != 0:
        return error_response('追加预算必须是10的倍数', code=400)
    
    # 时长验证
    valid_durations = [0, 2, 6, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168]  # 最多7天
    if duration not in valid_durations:
        return error_response(f'延长时长必须是以下值之一：{valid_durations}', code=400)
    
    db = SessionLocal()
    try:
        # 1. 查询订单信息
        order_sql = text("""
            SELECT o.id, o.order_id, o.account_id, o.status, a.aweme_sec_uid, a.access_token
            FROM douplus_order o
            INNER JOIN douyin_account a ON o.account_id = a.id
            WHERE o.id = :order_id AND o.user_id = :user_id AND o.deleted = 0
        """)
        
        order = db.execute(order_sql, {
            'order_id': order_id,
            'user_id': user_id
        }).fetchone()
        
        if not order:
            return error_response('订单不存在或无权限', code=404)
        
        order_internal_id, task_id, account_id, status, aweme_sec_uid, access_token = order
        
        # 2. 验证订单状态（只有投放中的订单可以续费）
        if status not in ['DELIVERING', 'RUNNING']:
            return error_response(f'订单状态为{status}，不允许续费', code=400)
        
        # 3. 验证投放密码
        user_sql = text("""
            SELECT invest_password FROM sys_user WHERE id = :user_id
        """)
        
        user = db.execute(user_sql, {'user_id': user_id}).fetchone()
        
        if not user or not user[0]:
            # 投放密码未设置，暂时允许（用于测试）
            logger.warning(f"用户{user_id}未设置投放密码，允许续费操作")
        else:
            # 解密数据库中的密码并比对（假设使用Base64编码）
            try:
                stored_password = decrypt_access_token(user[0])
                if invest_password != stored_password:
                    return error_response('投放密码错误', code=401)
            except:
                # 如果解密失败，直接比对
                if invest_password != user[0]:
                    return error_response('投放密码错误', code=401)
        
        # 4. 调用抖音DOU+续费API
        client = DouyinClient(access_token)
        
        try:
            # 将元转为分
            renewal_budget = int(budget * 100)
            
            result = client.renew_order(
                aweme_sec_uid=aweme_sec_uid,
                task_id=task_id,
                renewal_budget=renewal_budget,
                renewal_delivery_hour=duration
            )
            
            logger.info(f"订单续费成功: order_id={order_id}, task_id={task_id}")
            
            # 5. 记录续费操作（可选：创建续费记录表）
            # TODO: 记录续费历史
            
            return success_response(
                data=result,
                message=f'续费成功！已追加{budget}元预算' + (f'，延长{duration}小时' if duration > 0 else '')
            )
            
        except DouyinAPIError as e:
            logger.error(f"DOU+续费API调用失败: {e}")
            return error_response(f'续费失败：{str(e)}', code=500)
        finally:
            client.close()
            
    except Exception as e:
        logger.error(f"续费失败: {str(e)}")
        return error_response(f'系统错误：{str(e)}', code=500)
    finally:
        db.close()


@order_bp.route('/batch-renew', methods=['POST'])
@require_auth
def batch_renew_orders():
    """
    批量续费DOU+订单
    
    请求参数：
    - orderIds: 订单ID列表 (order_id字段，非内部ID)
    - budget: 每个订单追加的预算（元）
    - duration: 每个订单延长的时长（小时）
    - investPassword: 投放密码（可选）
    
    返回：
    - successCount: 成功续费的订单数
    - failedCount: 失败的订单数
    - details: 每个订单的处理结果
    """
    user_id = request.user_id
    data = request.json
    
    order_ids = data.get('orderIds', [])  # order_id列表
    budget = float(data.get('budget', 0))
    duration = float(data.get('duration', 0))
    invest_password = data.get('investPassword')
    
    logger.info(f"收到批量续费请求: user_id={user_id}, order_count={len(order_ids)}, budget={budget}, duration={duration}")
    
    # 1. 参数验证
    if not order_ids or len(order_ids) == 0:
        return error_response('订单ID列表不能为空', code=400)
    
    if budget <= 0:
        return error_response('追加预算必须大于0', code=400)
    
    db = SessionLocal()
    success_count = 0
    failed_count = 0
    details = []
    
    try:
        # 2. 获取投放密码
        password_sql = text("""
            SELECT invest_password_encrypted FROM sys_user 
            WHERE id = :user_id
        """)
        password_result = db.execute(password_sql, {'user_id': user_id}).fetchone()
        
        if not password_result or not password_result[0]:
            logger.warning(f"用户{user_id}未设置投放密码，允许批量续费操作")
            stored_password = None
        else:
            stored_password = password_result[0]
            
            # 验证投放密码
            if invest_password:
                from app.utils.crypto import hash_password
                input_hash = hash_password(invest_password)
                if input_hash != stored_password:
                    return error_response('投放密码错误', code=401)
        
        # 3. 遍历处理每个订单
        for order_id in order_ids:
            try:
                # 3.1 查询订单信息
                order_sql = text("""
                    SELECT o.order_id, o.status, a.open_id, a.access_token_encrypted, a.advertiser_id
                    FROM douplus_order o
                    JOIN douyin_account a ON o.account_id = a.id
                    WHERE o.order_id = :order_id AND o.user_id = :user_id AND o.deleted = 0
                """)
                order = db.execute(order_sql, {'order_id': order_id, 'user_id': user_id}).fetchone()
                
                if not order:
                    details.append({
                        'orderId': order_id,
                        'success': False,
                        'message': '订单不存在或无权操作'
                    })
                    failed_count += 1
                    continue
                
                dy_order_id, status, open_id, token_encrypted, advertiser_id = order
                
                # 3.2 验证订单状态
                if status not in ['DELIVERING', 'RUNNING']:
                    details.append({
                        'orderId': order_id,
                        'success': False,
                        'message': f'订单状态为{status}，不允许续费'
                    })
                    failed_count += 1
                    continue
                
                # 3.3 解密Access Token
                access_token = decrypt_access_token(token_encrypted)
                
                # 3.4 调用抖音DOU+续费API
                client = DouyinClient(
                    app_id=None,  # 从环境变量读取
                    app_secret=None,
                    access_token=access_token,
                    open_id=open_id
                )
                
                client.advertiser_id = advertiser_id
                
                result = client.renew_order(
                    order_id=dy_order_id,
                    budget=budget,
                    duration=duration
                )
                
                details.append({
                    'orderId': order_id,
                    'success': True,
                    'message': f'续费成功！已追加{budget}元预算' + (f'，延长{duration}小时' if duration > 0 else '')
                })
                success_count += 1
                logger.info(f"订单续费成功: order_id={order_id}")
                
                client.close()
                
            except DouyinAPIError as e:
                logger.error(f"订单{order_id}续费失败: {e}")
                details.append({
                    'orderId': order_id,
                    'success': False,
                    'message': f'续费失败：{str(e)}'
                })
                failed_count += 1
            except Exception as e:
                logger.error(f"订单{order_id}处理异常: {e}")
                details.append({
                    'orderId': order_id,
                    'success': False,
                    'message': f'处理异常：{str(e)}'
                })
                failed_count += 1
        
        # 4. 返回汇总结果
        return success_response(
            data={
                'successCount': success_count,
                'failedCount': failed_count,
                'totalCount': len(order_ids),
                'details': details
            },
            message=f'批量续费完成：成功{success_count}个，失败{failed_count}个'
        )
        
    except Exception as e:
        logger.error(f"批量续费失败: {str(e)}")
        return error_response(f'系统错误：{str(e)}', code=500)
    finally:
        db.close()
