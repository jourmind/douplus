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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
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

    /**
     * 获取DOU+订单列表（v3.0 API）
     * 使用aweme_sec_uid替代advertiser_id
     */
    public DouplusOrderListResult getDouplusOrderListV3(String accessToken, String awemeSecUid, int page, int pageSize) {
        String url = "https://api.oceanengine.com/open_api/v3.0/douplus/order/list/";
        
        StringBuilder urlBuilder = new StringBuilder(url);
        urlBuilder.append("?aweme_sec_uid=").append(awemeSecUid);
        urlBuilder.append("&page=").append(page);
        urlBuilder.append("&page_size=").append(pageSize);

        HttpHeaders headers = new HttpHeaders();
        headers.set("Access-Token", accessToken);
        headers.setContentType(MediaType.APPLICATION_JSON);

        try {
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    urlBuilder.toString(), HttpMethod.GET, entity, String.class);
            
            JSONObject json = JSON.parseObject(response.getBody());
            log.info("DOU+ Order List V3 Response code: {}, message: {}", 
                    json.getIntValue("code", -1), json.getString("message"));
            
            int errCode = json.getIntValue("code", -1);
            if (errCode != 0) {
                String errMsg = json.getString("message");
                log.error("获取DOU+订单列表失败(v3.0): code={}, msg={}", errCode, errMsg);
                throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, errMsg);
            }

            JSONObject data = json.getJSONObject("data");
            DouplusOrderListResult result = new DouplusOrderListResult();
            
            // v3.0 API: total_num在page_info中
            JSONObject pageInfo = data.getJSONObject("page_info");
            if (pageInfo != null) {
                result.setTotalCount(pageInfo.getIntValue("total_num", 0));
                result.setPageInfo(pageInfo);
            }
            
            List<DouplusOrderItem> orders = new ArrayList<>();
            // v3.0 API: 订单列表在order_list中
            if (data.containsKey("order_list") && data.getJSONArray("order_list") != null) {
                for (Object item : data.getJSONArray("order_list")) {
                    JSONObject orderWrapper = (JSONObject) item;
                    DouplusOrderItem order = parseOrderItemV3(orderWrapper);
                    if (order != null) {
                        orders.add(order);
                    }
                }
            }
            result.setOrders(orders);
            log.info("成功获取{}条订单，总计{}条", orders.size(), result.getTotalCount());
            return result;
            
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("获取DOU+订单列表异常(v3.0)", e);
            throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, "获取订单列表失败: " + e.getMessage());
        }
    }

    /**
     * 解析v3.0 API的订单项
     */
    private DouplusOrderItem parseOrderItemV3(JSONObject orderWrapper) {
        try {
            DouplusOrderItem item = new DouplusOrderItem();
            
            // 打印完整的订单数据用于调试
            log.info("========== 解析订单原始数据 ==========");
            log.info("orderWrapper keys: {}", orderWrapper.keySet());
            
            // 订单基本信息在order字段中
            JSONObject orderInfo = orderWrapper.getJSONObject("order");
            if (orderInfo != null) {
                log.info("orderInfo keys: {}", orderInfo.keySet());
                log.info("orderInfo全部数据: {}", orderInfo.toJSONString());
                item.setOrderId(String.valueOf(orderInfo.getLongValue("order_id", 0)));
                item.setBudget(BigDecimal.valueOf(orderInfo.getLongValue("budget", 0) / 100.0));
                item.setCreateTime(orderInfo.getString("order_create_time"));
                item.setStatus(orderInfo.getString("task_status"));
                log.info("订单ID: {}, 状态: {}", item.getOrderId(), item.getStatus());
            }
            
            // 视频信息在item_info_list中
            if (orderWrapper.containsKey("item_info_list") && orderWrapper.getJSONArray("item_info_list") != null) {
                var itemInfoList = orderWrapper.getJSONArray("item_info_list");
                log.info("item_info_list大小: {}", itemInfoList.size());
                if (!itemInfoList.isEmpty()) {
                    JSONObject itemInfo = itemInfoList.getJSONObject(0);
                    log.info("itemInfo keys: {}", itemInfo.keySet());
                    log.info("itemInfo全部数据: {}", itemInfo.toJSONString());
                    item.setAwemeId(String.valueOf(itemInfo.getLongValue("aweme_item_id", 0)));
                    item.setAwemeNick(itemInfo.getString("aweme_author_name"));
                    // 视频标题 - v3.0 API字段名是 aweme_item_title
                    String title = itemInfo.getString("aweme_item_title");
                    if (title == null) title = itemInfo.getString("aweme_title");
                    if (title == null) title = itemInfo.getString("title");
                    item.setAwemeTitle(title);
                    log.info("解析视频标题: {}", item.getAwemeTitle());
                    // 视频封面 - v3.0 API字段名是 aweme_item_cover
                    var covers = itemInfo.getJSONArray("aweme_item_cover");
                    if (covers == null) covers = itemInfo.getJSONArray("aweme_cover");
                    if (covers == null) covers = itemInfo.getJSONArray("cover");
                    if (covers != null && !covers.isEmpty()) {
                        item.setAwemeCover(covers.getString(0));
                        log.info("解析视频封面(数组): {}", item.getAwemeCover());
                    } else {
                        // 尝试作为字符串获取
                        String coverStr = itemInfo.getString("aweme_cover");
                        if (coverStr == null) coverStr = itemInfo.getString("cover");
                        if (coverStr == null) coverStr = itemInfo.getString("cover_url");
                        if (coverStr != null) {
                            item.setAwemeCover(coverStr);
                            log.info("解析视频封面(字符串): {}", item.getAwemeCover());
                        }
                    }
                    // 头像是数组，取第一个
                    var avatars = itemInfo.getJSONArray("aweme_author_avatar");
                    if (avatars != null && !avatars.isEmpty()) {
                        item.setAwemeAvatar(avatars.getString(0));
                    }
                }
            } else {
                log.warn("订单{}无item_info_list，原始数据: {}", item.getOrderId(), orderWrapper.toJSONString());
            }
            
            // 广告投放信息在ad_list中
            if (orderWrapper.containsKey("ad_list") && orderWrapper.getJSONArray("ad_list") != null) {
                var adList = orderWrapper.getJSONArray("ad_list");
                log.info("ad_list大小: {}", adList.size());
                if (!adList.isEmpty()) {
                    JSONObject adInfo = adList.getJSONObject(0);
                    log.info("adInfo keys: {}", adInfo.keySet());
                    log.info("adInfo全部数据: {}", adInfo.toJSONString());
                    item.setDuration(adInfo.getIntValue("delivery_time", 24));
                    item.setGoalType(adInfo.getString("delivery_type"));
                    // v3.0的budget在ad_list中也有
                    if (item.getBudget() == null || item.getBudget().compareTo(BigDecimal.ZERO) == 0) {
                        item.setBudget(BigDecimal.valueOf(adInfo.getLongValue("budget", 0) / 100.0));
                    }
                    // 尝试从ad_list中获取统计数据
                    if (adInfo.containsKey("stat_cost")) {
                        item.setActualCost(BigDecimal.valueOf(adInfo.getLongValue("stat_cost", 0) / 100.0));
                        log.info("从ad_list获取消耗: {}", item.getActualCost());
                    }
                    if (adInfo.containsKey("show_cnt")) {
                        item.setPlayCount(adInfo.getIntValue("show_cnt", 0));
                        log.info("从ad_list获取播放量: {}", item.getPlayCount());
                    }
                }
            }
            
            // 统计数据在data_summary中
            if (orderWrapper.containsKey("data_summary") && orderWrapper.getJSONObject("data_summary") != null) {
                JSONObject dataSummary = orderWrapper.getJSONObject("data_summary");
                log.info("解析data_summary: {}", dataSummary.toJSONString());
                // 消耗金额（单位：分）
                item.setActualCost(BigDecimal.valueOf(dataSummary.getLongValue("stat_cost", 0) / 100.0));
                // 播放量
                item.setPlayCount(dataSummary.getIntValue("play_cnt", 0));
                // 点赞量
                item.setLikeCount(dataSummary.getIntValue("like_cnt", 0));
                // 评论量
                item.setCommentCount(dataSummary.getIntValue("comment_cnt", 0));
                // 转发量
                item.setShareCount(dataSummary.getIntValue("share_cnt", 0));
                // 新增粉丝
                item.setFollowCount(dataSummary.getIntValue("follow_cnt", 0));
                // 组件点击/转化量
                item.setClickCount(dataSummary.getIntValue("convert_cnt", 0));
            } else {
                log.warn("订单{}无data_summary", item.getOrderId());
            }
            
            // 默认值
            if (item.getActualCost() == null) item.setActualCost(BigDecimal.ZERO);
            if (item.getPlayCount() == null) item.setPlayCount(0);
            if (item.getLikeCount() == null) item.setLikeCount(0);
            if (item.getCommentCount() == null) item.setCommentCount(0);
            if (item.getShareCount() == null) item.setShareCount(0);
            if (item.getFollowCount() == null) item.setFollowCount(0);
            if (item.getClickCount() == null) item.setClickCount(0);
            
            return item;
        } catch (Exception e) {
            log.warn("解析订单项失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 获取DOU+订单列表（旧版v2 API - 已废弃，仅作兼容）
     * @deprecated 使用 {@link #getDouplusOrderListV3} 代替
     */
    @Deprecated
    public DouplusOrderListResult getDouplusOrderList(String accessToken, String advertiserId, int page, int pageSize) {
        String url = "https://ad.oceanengine.com/open_api/2/douplus/order/list/";
        
        StringBuilder urlBuilder = new StringBuilder(url);
        urlBuilder.append("?advertiser_id=").append(advertiserId);
        urlBuilder.append("&page=").append(page);
        urlBuilder.append("&page_size=").append(pageSize);

        HttpHeaders headers = new HttpHeaders();
        headers.set("Access-Token", accessToken);
        headers.setContentType(MediaType.APPLICATION_JSON);

        try {
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    urlBuilder.toString(), HttpMethod.GET, entity, String.class);
            
            JSONObject json = JSON.parseObject(response.getBody());
            log.debug("DOU+ Order List Response: {}", json);
            
            int errCode = json.getIntValue("code", -1);
            if (errCode != 0) {
                String errMsg = json.getString("message");
                log.error("获取DOU+订单列表失败: code={}, msg={}", errCode, errMsg);
                throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, errMsg);
            }

            JSONObject data = json.getJSONObject("data");
            DouplusOrderListResult result = new DouplusOrderListResult();
            result.setTotalCount(data.getIntValue("total_count", 0));
            result.setPageInfo(data.getJSONObject("page_info"));
            
            List<DouplusOrderItem> orders = new ArrayList<>();
            if (data.containsKey("list") && data.getJSONArray("list") != null) {
                for (Object item : data.getJSONArray("list")) {
                    JSONObject orderJson = (JSONObject) item;
                    DouplusOrderItem order = parseOrderItem(orderJson);
                    orders.add(order);
                }
            }
            result.setOrders(orders);
            return result;
            
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("获取DOU+订单列表异常", e);
            throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, "获取订单列表失败: " + e.getMessage());
        }
    }

    /**
     * 解析订单项
     */
    private DouplusOrderItem parseOrderItem(JSONObject orderJson) {
        DouplusOrderItem order = new DouplusOrderItem();
        
        // 输出原始数据用于调试
        log.info("解析DOU+订单原始数据: {}", orderJson.toJSONString());
        
        order.setOrderId(orderJson.getString("order_id"));
        order.setAwemeId(orderJson.getString("aweme_id"));
        order.setAwemeNick(orderJson.getString("aweme_nick"));
        order.setAwemeAvatar(orderJson.getString("aweme_avatar"));
        order.setStatus(orderJson.getString("status"));
        order.setBudget(BigDecimal.valueOf(orderJson.getLongValue("budget", 0) / 100.0));
        order.setActualCost(BigDecimal.valueOf(orderJson.getLongValue("actual_cost", 0) / 100.0));
        
        // 尝试多种字段名解析播放量
        int playCount = orderJson.getIntValue("play_count", 0);
        if (playCount == 0) playCount = orderJson.getIntValue("show_cnt", 0);
        if (playCount == 0) playCount = orderJson.getIntValue("play_cnt", 0);
        if (playCount == 0) playCount = orderJson.getIntValue("total_play", 0);
        // 检柯effect_info子对象
        if (playCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                playCount = effectInfo.getIntValue("play_count", 0);
                if (playCount == 0) playCount = effectInfo.getIntValue("show_cnt", 0);
            }
        }
        order.setPlayCount(playCount);
        
        // 点赞量
        int likeCount = orderJson.getIntValue("like_count", 0);
        if (likeCount == 0) likeCount = orderJson.getIntValue("like_cnt", 0);
        if (likeCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                likeCount = effectInfo.getIntValue("like_count", 0);
            }
        }
        order.setLikeCount(likeCount);
        
        // 评论量
        int commentCount = orderJson.getIntValue("comment_count", 0);
        if (commentCount == 0) commentCount = orderJson.getIntValue("comment_cnt", 0);
        if (commentCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                commentCount = effectInfo.getIntValue("comment_count", 0);
            }
        }
        order.setCommentCount(commentCount);
        
        // 转发量
        int shareCount = orderJson.getIntValue("share_count", 0);
        if (shareCount == 0) shareCount = orderJson.getIntValue("share_cnt", 0);
        if (shareCount == 0) shareCount = orderJson.getIntValue("forward_count", 0);
        if (shareCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                shareCount = effectInfo.getIntValue("share_count", 0);
            }
        }
        order.setShareCount(shareCount);
        
        // 新增粉丝
        int followCount = orderJson.getIntValue("follow_count", 0);
        if (followCount == 0) followCount = orderJson.getIntValue("follow_cnt", 0);
        if (followCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                followCount = effectInfo.getIntValue("follow_count", 0);
            }
        }
        order.setFollowCount(followCount);
        
        // 点击量
        int clickCount = orderJson.getIntValue("click_count", 0);
        if (clickCount == 0) clickCount = orderJson.getIntValue("click_cnt", 0);
        if (clickCount == 0) clickCount = orderJson.getIntValue("convert_cnt", 0);
        if (clickCount == 0 && orderJson.containsKey("effect_info")) {
            JSONObject effectInfo = orderJson.getJSONObject("effect_info");
            if (effectInfo != null) {
                clickCount = effectInfo.getIntValue("click_count", 0);
            }
        }
        order.setClickCount(clickCount);
        
        order.setDuration(orderJson.getIntValue("duration", 24));
        order.setCreateTime(orderJson.getString("create_time"));
        order.setStartTime(orderJson.getString("start_time"));
        order.setEndTime(orderJson.getString("end_time"));
        order.setGoalType(orderJson.getString("goal_type"));
        
        // 解析视频信息 - 尝试多种字段名
        String awemeTitle = orderJson.getString("aweme_title");
        if (awemeTitle == null) awemeTitle = orderJson.getString("title");
        if (awemeTitle == null) awemeTitle = orderJson.getString("video_title");
        if (awemeTitle == null && orderJson.containsKey("aweme_info")) {
            JSONObject awemeInfo = orderJson.getJSONObject("aweme_info");
            if (awemeInfo != null) {
                awemeTitle = awemeInfo.getString("title");
                if (awemeTitle == null) awemeTitle = awemeInfo.getString("aweme_title");
            }
        }
        order.setAwemeTitle(awemeTitle);
        
        String awemeCover = orderJson.getString("aweme_cover");
        if (awemeCover == null) awemeCover = orderJson.getString("cover");
        if (awemeCover == null) awemeCover = orderJson.getString("video_cover");
        if (awemeCover == null && orderJson.containsKey("aweme_info")) {
            JSONObject awemeInfo = orderJson.getJSONObject("aweme_info");
            if (awemeInfo != null) {
                awemeCover = awemeInfo.getString("cover");
                if (awemeCover == null) awemeCover = awemeInfo.getString("aweme_cover");
            }
        }
        order.setAwemeCover(awemeCover);
        
        log.info("解析订单{}: 播放={}, 点赞={}, 转发={}, 点击={}, 消耗={}", 
                order.getOrderId(), playCount, likeCount, shareCount, clickCount, order.getActualCost());
        
        return order;
    }

    @Data
    public static class DouplusOrderListResult {
        private int totalCount;
        private JSONObject pageInfo;
        private List<DouplusOrderItem> orders;
    }

    @Data
    public static class DouplusOrderItem {
        private String orderId;
        private String awemeId;
        private String awemeNick;
        private String awemeAvatar;
        private String awemeTitle;   // 视频标题
        private String awemeCover;   // 视频封面
        private String status;
        private BigDecimal budget;
        private BigDecimal actualCost;
        private Integer playCount;
        private Integer likeCount;
        private Integer commentCount;
        private Integer shareCount;
        private Integer followCount;
        private Integer clickCount;
        private Integer duration;
        private String createTime;
        private String startTime;
        private String endTime;
        private String goalType;
    }

    /**
     * 获取DOU+订单效果报告（v3.0 API）
     * 获取播放量、点赞量、转发量、消耗等统计数据
     * API: /open_api/v3.0/douplus/order/report/
     * 方法: GET
     * 必填: Access-Token(header), aweme_sec_uid, stat_time(JSON格式)
     */
    public DouplusOrderReportResult getDouplusOrderReport(String accessToken, String awemeSecUid, 
            List<Long> orderIds, String beginTime, String endTime) {
        
        DouplusOrderReportResult result = new DouplusOrderReportResult();
        Map<String, DouplusOrderStats> allStats = new HashMap<>();
        
        int page = 1;
        int pageSize = 100;
        int totalPage = 1;
        
        try {
            // stat_time参数必须用URL编码的JSON格式传递
            String statTimeJson = String.format("{\"begin_time\":\"%s\",\"end_time\":\"%s\"}", beginTime, endTime);
            String encodedStatTime = java.net.URLEncoder.encode(statTimeJson, "UTF-8");
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("Access-Token", accessToken);
            
            // 分页循环获取所有数据
            while (page <= totalPage) {
                // 构建完整URL字符串（已包含编码的stat_time）
                String urlStr = "https://api.oceanengine.com/open_api/v3.0/douplus/order/report/"
                        + "?aweme_sec_uid=" + awemeSecUid
                        + "&stat_time=" + encodedStatTime
                        + "&page=" + page
                        + "&page_size=" + pageSize;
                
                log.info("调用DOU+订单报告API (GET) 第{}页: {}", page, urlStr);
                
                // 使用URI对象避免RestTemplate二次编码
                java.net.URI uri = new java.net.URI(urlStr);
                
                HttpEntity<String> entity = new HttpEntity<>(headers);
                ResponseEntity<String> response = restTemplate.exchange(
                        uri, HttpMethod.GET, entity, String.class);
                
                JSONObject json = JSON.parseObject(response.getBody());
                
                int errCode = json.getIntValue("code", -1);
                if (errCode != 0) {
                    String errMsg = json.getString("message");
                    log.error("获取DOU+订单报告失败(v3.0): code={}, msg={}", errCode, errMsg);
                    break;
                }
    
                JSONObject data = json.getJSONObject("data");
                result.setRawData(data);
                
                // 获取分页信息
                if (data != null && data.containsKey("page_info")) {
                    JSONObject pageInfo = data.getJSONObject("page_info");
                    totalPage = pageInfo.getIntValue("total_page", 1);
                }
                
                // 解析当前页数据
                if (data != null && data.containsKey("order_metrics")) {
                    for (Object item : data.getJSONArray("order_metrics")) {
                        JSONObject reportItem = (JSONObject) item;
                        DouplusOrderStats stats = parseOrderStatsV3(reportItem);
                        if (stats != null && stats.getOrderId() != null) {
                            allStats.put(stats.getOrderId(), stats);
                        }
                    }
                    log.info("第{}页获取{}条数据，累计{}条", page, 
                            data.getJSONArray("order_metrics").size(), allStats.size());
                }
                
                page++;
                
                // 防止请求过快
                if (page <= totalPage) {
                    Thread.sleep(200);
                }
            }
            
            result.setOrderStats(allStats);
            log.info("效果报告API总共获取{}条订单数据", allStats.size());
            
        } catch (Exception e) {
            log.error("获取DOU+订单报告异常(v3.0)", e);
        }
        
        return result;
    }
    
    /**
     * 解析v3.0订单报告统计数据
     * 结构: { dimension_data: {order_id, ad_id, ...}, metrics_data: {total_play, dy_comment, ...} }
     */
    private DouplusOrderStats parseOrderStatsV3(JSONObject reportItem) {
        try {
            DouplusOrderStats stats = new DouplusOrderStats();
            
            // 订单ID在dimension_data中
            JSONObject dimensionData = reportItem.getJSONObject("dimension_data");
            if (dimensionData != null) {
                stats.setOrderId(String.valueOf(dimensionData.getLongValue("order_id", 0)));
            }
            
            // 效果数据在metrics_data中
            JSONObject metricsData = reportItem.getJSONObject("metrics_data");
            if (metricsData != null) {
                // 消耗金额（单位：分）
                stats.setStatCost(BigDecimal.valueOf(metricsData.getLongValue("stat_cost", 0) / 100.0));
                // 播放量 - v3.0字段名是total_play
                stats.setPlayCount(metricsData.getIntValue("total_play", 0));
                // 点赞量 - v3.0字段名是custom_like
                stats.setLikeCount(metricsData.getIntValue("custom_like", 0));
                // 评论量 - v3.0字段名是dy_comment
                stats.setCommentCount(metricsData.getIntValue("dy_comment", 0));
                // 转发量 - v3.0字段名是dy_share
                stats.setShareCount(metricsData.getIntValue("dy_share", 0));
                // 新增粉丝 - v3.0字段名是dy_follow
                stats.setFollowCount(metricsData.getIntValue("dy_follow", 0));
                // 主页访问
                int homeVisited = metricsData.getIntValue("dy_home_visited", 0);
                // 转化量
                int convertCnt = metricsData.getIntValue("dp_target_convert_cnt", 0);
                stats.setClickCount(convertCnt > 0 ? convertCnt : homeVisited);
                
                log.debug("解析订单{}: 播放={}, 点赞={}, 评论={}, 转发={}, 关注={}, 消耗={}",
                        stats.getOrderId(), stats.getPlayCount(), stats.getLikeCount(),
                        stats.getCommentCount(), stats.getShareCount(), stats.getFollowCount(),
                        stats.getStatCost());
            }
            
            return stats;
        } catch (Exception e) {
            log.warn("解析订单统计数据失败: {}", e.getMessage());
            return null;
        }
    }

    @Data
    public static class DouplusOrderReportResult {
        private JSONObject rawData;
        private Map<String, DouplusOrderStats> orderStats = new HashMap<>();
    }

    @Data
    public static class DouplusOrderStats {
        private String orderId;
        private BigDecimal statCost;  // 消耗金额
        private Integer playCount;    // 播放量
        private Integer likeCount;    // 点赞量
        private Integer commentCount; // 评论量
        private Integer shareCount;   // 转发量
        private Integer followCount;  // 新增粉丝
        private Integer clickCount;   // 组件点击
    }
}
