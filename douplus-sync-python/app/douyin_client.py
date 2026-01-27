"""
抖音DOU+ API客户端
"""
import httpx
from typing import Optional, List, Dict, Any
from loguru import logger


class DouyinAPIError(Exception):
    """抖音API异常"""
    pass


class DouyinClient:
    """抖音API客户端"""
    
    BASE_URL = "https://api.oceanengine.com/open_api/v3.0"
    
    def __init__(self, access_token: str):
        """
        初始化客户端
        
        Args:
            access_token: 访问令牌
        """
        self.access_token = access_token
        self.client = httpx.Client(timeout=30.0)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他参数
        
        Returns:
            API响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            data = response.json()
            code = data.get("code", -1)
            
            if code != 0:
                error_msg = data.get("message", "Unknown error")
                raise DouyinAPIError(f"API错误: code={code}, message={error_msg}")
            
            return data.get("data", {})
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP请求失败: {e}")
            raise DouyinAPIError(f"HTTP请求失败: {e}")
    
    def get_order_list(
        self,
        aweme_sec_uid: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取DOU+订单列表
        
        Args:
            aweme_sec_uid: 账号secUid
            page: 页码
            page_size: 每页数量
        
        Returns:
            订单列表
        """
        endpoint = "/douplus/order/list/"
        
        params = {
            "aweme_sec_uid": aweme_sec_uid,
            "page": page,
            "page_size": page_size
        }
        
        logger.info(f"调用订单列表API: aweme_sec_uid={aweme_sec_uid}, page={page}")
        
        data = self._request("GET", endpoint, params=params)
        # 修复：API返回的字段是order_list，不是list
        orders = data.get("order_list", [])
        
        # 打印完整响应用于调试
        logger.info(f"API响应数据keys: {list(data.keys())}")
        logger.info(f"获取到{len(orders)}条订单")
        
        # 如果没有订单但有page_info，说明结构正确但列表为空
        if not orders and "page_info" in data:
            total_num = data.get("page_info", {}).get("total_num", 0)
            logger.warning(f"订单列表为空，但total_num={total_num}，可能是数据结构问题")
        
        return orders
    
    def get_order_report(
        self,
        aweme_sec_uid: str,
        order_ids: Optional[List[str]] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取订单效果数据
        
        Args:
            aweme_sec_uid: 账号secUid
            order_ids: 订单ID列表(可选)
            begin_time: 开始时间 YYYY-MM-DD
            end_time: 结束时间 YYYY-MM-DD
        
        Returns:
            订单效果数据字典 {order_id: stats}
        """
        endpoint = "/douplus/order/report/"
        
        json_data = {
            "aweme_sec_uid": aweme_sec_uid
        }
        
        if order_ids:
            json_data["order_ids"] = order_ids
        if begin_time:
            json_data["begin_time"] = begin_time
        if end_time:
            json_data["end_time"] = end_time
        
        logger.info(f"调用效果报告API: aweme_sec_uid={aweme_sec_uid}, "
                   f"order_count={len(order_ids) if order_ids else 'all'}")
        
        data = self._request("POST", endpoint, json=json_data)
        
        # 解析返回数据
        result = {}
        for item in data.get("data", []):
            dimension = item.get("dimension_data", {})
            metrics = item.get("metrics_data", {})
            
            order_id = dimension.get("order_id")
            if order_id:
                result[order_id] = {
                    "order_id": order_id,
                    "item_id": dimension.get("item_id"),
                    "stat_cost": metrics.get("stat_cost", 0) / 100.0,  # 分转元
                    "total_play": metrics.get("total_play", 0),
                    "custom_like": metrics.get("custom_like", 0),
                    "dy_comment": metrics.get("dy_comment", 0),
                    "dy_share": metrics.get("dy_share", 0),
                    "dy_follow": metrics.get("dy_follow", 0),
                    "play_duration_5s_rank": metrics.get("play_duration_5s_rank", 0),
                    "dy_home_visited": metrics.get("dy_home_visited", 0),
                    "dp_target_convert_cnt": metrics.get("dp_target_convert_cnt", 0),
                    "custom_convert_cost": metrics.get("custom_convert_cost", 0) / 100.0,  # 分转元
                    "show_cnt": metrics.get("show_cnt", 0),
                    "live_click_source_cnt": metrics.get("live_click_source_cnt", 0),
                    "live_gift_uv": metrics.get("live_gift_uv", 0),
                    "live_gift_amount": metrics.get("live_gift_amount", 0) / 100.0,
                    "live_comment_cnt": metrics.get("live_comment_cnt", 0),
                    "live_follow_count": metrics.get("douplus_live_follow_count", 0),
                    "live_gift_cnt": metrics.get("live_gift_cnt", 0),
                }
        
        logger.info(f"获取到{len(result)}条效果数据")
        return result
    
    def renew_order(
        self,
        aweme_sec_uid: str,
        task_id: str,
        renewal_budget: int,
        renewal_delivery_hour: float
    ) -> Dict[str, Any]:
        """
        续费DOU+订单（追加预算和时长）
        
        Args:
            aweme_sec_uid: 抖音号ID
            task_id: 订单ID（PC端订单号）
            renewal_budget: 追加投放预算（单位：分，需为10的倍数，范围10,000-500,000,000）
            renewal_delivery_hour: 延长投放时长（小时，支持0、2、6、12、24或12的倍数，最大720）
        
        Returns:
            API响应数据
        
        注意：
        - 不可以仅增加投放时长（renewal_budget必须>0）
        - 可以仅增加投放预算（renewal_delivery_hour可以为0）
        """
        endpoint = "/douplus/order/renew/"
        
        json_data = {
            "aweme_sec_uid": aweme_sec_uid,
            "task_id": int(task_id),
            "renewal_budget": renewal_budget,
            "renewal_delivery_hour": renewal_delivery_hour
        }
        
        logger.info(f"调用续费API: task_id={task_id}, budget={renewal_budget/100}元, hour={renewal_delivery_hour}")
        
        try:
            data = self._request("POST", endpoint, json=json_data)
            logger.info(f"续费成功: {data}")
            return data
        except DouyinAPIError as e:
            logger.error(f"续费失败: {e}")
            raise
    
    def close(self):
        """关闭客户端"""
        self.client.close()
