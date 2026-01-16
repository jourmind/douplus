package com.douplus.douplus.client;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.ResultCode;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

/**
 * 抖音DOU+投放API客户端
 * 
 * 说明：这是一个抽象封装层，实际调用需要根据抖音官方API文档调整
 * 官方文档：https://developer.open-douyin.com/
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DouyinAdClient {

    @Value("${douyin.api.base-url}")
    private String baseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * 创建DOU+投放订单
     */
    public CreateOrderResult createOrder(String accessToken, CreateOrderRequest request) {
        String url = baseUrl + "/dou+/order/create/"; // 示例路径，需根据实际API调整
        
        Map<String, Object> params = new HashMap<>();
        params.put("item_id", request.getItemId());
        params.put("budget", request.getBudget().intValue() * 100); // 转为分
        params.put("duration", request.getDuration());
        params.put("target_type", request.getTargetType());
        
        if (request.getTargetConfig() != null) {
            params.put("target_config", request.getTargetConfig());
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("access-token", accessToken);

        try {
            HttpEntity<String> entity = new HttpEntity<>(JSON.toJSONString(params), headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, entity, String.class);
            
            JSONObject json = JSON.parseObject(response.getBody());
            
            // 检查返回结果
            int errCode = json.getIntValue("err_no", -1);
            if (errCode != 0) {
                String errMsg = json.getString("err_msg");
                log.error("抖音API调用失败: code={}, msg={}", errCode, errMsg);
                throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, errMsg);
            }

            JSONObject data = json.getJSONObject("data");
            CreateOrderResult result = new CreateOrderResult();
            result.setOrderId(data.getString("order_id"));
            result.setExpectedExposure(data.getIntValue("expected_exposure", 0));
            return result;
            
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("调用抖音API异常", e);
            throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, "调用抖音API失败: " + e.getMessage());
        }
    }

    /**
     * 查询DOU+订单状态
     */
    public OrderStatusResult queryOrderStatus(String accessToken, String orderId) {
        String url = baseUrl + "/dou+/order/status/?order_id=" + orderId;
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("access-token", accessToken);

        try {
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
            
            JSONObject json = JSON.parseObject(response.getBody());
            int errCode = json.getIntValue("err_no", -1);
            if (errCode != 0) {
                throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, json.getString("err_msg"));
            }

            JSONObject data = json.getJSONObject("data");
            OrderStatusResult result = new OrderStatusResult();
            result.setOrderId(orderId);
            result.setStatus(data.getString("status"));
            result.setActualCost(BigDecimal.valueOf(data.getLongValue("actual_cost", 0) / 100.0));
            result.setActualExposure(data.getIntValue("actual_exposure", 0));
            return result;
            
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("查询订单状态异常", e);
            throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, "查询订单状态失败");
        }
    }

    /**
     * 取消DOU+订单
     */
    public boolean cancelOrder(String accessToken, String orderId) {
        String url = baseUrl + "/dou+/order/cancel/";
        
        Map<String, Object> params = new HashMap<>();
        params.put("order_id", orderId);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("access-token", accessToken);

        try {
            HttpEntity<String> entity = new HttpEntity<>(JSON.toJSONString(params), headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, entity, String.class);
            
            JSONObject json = JSON.parseObject(response.getBody());
            return json.getIntValue("err_no", -1) == 0;
            
        } catch (Exception e) {
            log.error("取消订单异常", e);
            return false;
        }
    }

    // ======== 请求/响应类 ========

    @Data
    public static class CreateOrderRequest {
        private String itemId;
        private BigDecimal budget;
        private Integer duration;
        private Integer targetType;
        private String targetConfig;
    }

    @Data
    public static class CreateOrderResult {
        private String orderId;
        private Integer expectedExposure;
    }

    @Data
    public static class OrderStatusResult {
        private String orderId;
        private String status;
        private BigDecimal actualCost;
        private Integer actualExposure;
    }
}
