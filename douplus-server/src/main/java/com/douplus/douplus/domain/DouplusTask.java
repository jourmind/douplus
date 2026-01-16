package com.douplus.douplus.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.douplus.common.domain.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DOU+投放任务实体
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("douplus_task")
public class DouplusTask extends BaseEntity {

    /**
     * 创建用户ID
     */
    private Long userId;

    /**
     * 抖音账号ID
     */
    private Long accountId;

    /**
     * 视频ID（关联douyin_video）
     */
    private Long videoId;

    /**
     * 抖音视频ID
     */
    private String itemId;

    /**
     * 任务类型：1-视频投放，2-直播投放
     */
    private Integer taskType;

    /**
     * 投放目标：1-系统智能推荐，2-自定义定向
     */
    private Integer targetType;

    /**
     * 投放时长(小时)
     */
    private Integer duration;

    /**
     * 投放预算(元)
     */
    private BigDecimal budget;

    /**
     * 实际消耗
     */
    private BigDecimal actualCost;

    /**
     * 预计曝光量
     */
    private Integer expectedExposure;

    /**
     * 实际曝光量
     */
    private Integer actualExposure;

    /**
     * 状态：WAIT-待执行，RUNNING-执行中，SUCCESS-成功，FAIL-失败，CANCELLED-已取消
     */
    private String status;

    /**
     * 抖音订单ID
     */
    private String orderId;

    /**
     * 重试次数
     */
    private Integer retryCount;

    /**
     * 最大重试次数
     */
    private Integer maxRetry;

    /**
     * 错误信息
     */
    private String errorMsg;

    /**
     * 计划执行时间
     */
    private LocalDateTime scheduledTime;

    /**
     * 实际执行时间
     */
    private LocalDateTime executedTime;

    /**
     * 完成时间
     */
    private LocalDateTime completedTime;

    /**
     * 定向配置(JSON)
     */
    private String targetConfig;

    // ======== 任务状态常量 ========
    public static final String STATUS_WAIT = "WAIT";
    public static final String STATUS_RUNNING = "RUNNING";
    public static final String STATUS_SUCCESS = "SUCCESS";
    public static final String STATUS_FAIL = "FAIL";
    public static final String STATUS_CANCELLED = "CANCELLED";
}
