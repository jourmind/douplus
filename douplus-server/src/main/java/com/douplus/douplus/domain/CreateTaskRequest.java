package com.douplus.douplus.domain;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 创建投放任务请求
 */
@Data
public class CreateTaskRequest {

    /**
     * 抖音账号ID
     */
    @NotNull(message = "请选择付款抖音号")
    private Long accountId;

    /**
     * 目标抖音账号ID（被投账号）
     */
    private Long targetAccountId;

    /**
     * 抖音视频ID
     */
    @NotBlank(message = "请选择被投视频")
    private String itemId;

    /**
     * 任务类型：1-视频投放，2-直播投放
     */
    private Integer taskType = 1;

    /**
     * 投放目标：1-系统智能推荐，2-自定义定向
     */
    private Integer targetType = 1;

    /**
     * 我想要：CONTENT_HEAT-内容加热，FANS-粉丝经营，CUSTOMER-获取客户，PRODUCT-商品营销，APP-应用营销
     */
    private String wantType = "CONTENT_HEAT";

    /**
     * 更想获得：LIKE_COMMENT-点赞评论量，QUALITY_INTERACT-高质量互动，HOME_VIEW-主页浏览量，
     * LINK_CLICK-评论链接点击，VIDEO_PLAY-视频播放量，LIVE_POPULARITY-直播间人气
     */
    private String objective = "LIKE_COMMENT";

    /**
     * 投放策略：GUARANTEE_PLAY-保证播放量，MAX_LIKE_COMMENT-最大点赞评论量
     */
    private String strategy = "GUARANTEE_PLAY";

    /**
     * 投放时长(小时)
     */
    private Integer duration = 24;

    /**
     * 投放预算(元)
     */
    @NotNull(message = "请输入投放金额")
    @DecimalMin(value = "100", message = "单笔投放金额不能低于100元")
    private BigDecimal budget;

    /**
     * 投放笔数（一次创建多笔相同订单）
     */
    private Integer count = 1;

    /**
     * 预定投放时间（为空则立即执行）
     */
    private LocalDateTime scheduledTime;

    /**
     * 自定义投放时段开始时间
     */
    private String customTimeStart;

    /**
     * 自定义投放时段结束时间
     */
    private String customTimeEnd;

    /**
     * 定向配置(JSON)
     */
    private String targetConfig;

    /**
     * 投放密码
     */
    @NotBlank(message = "请输入投放密码")
    private String investPassword;
}