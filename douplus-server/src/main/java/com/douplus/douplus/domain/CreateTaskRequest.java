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
     * 投放笔数
     */
    private Integer count = 1;

    /**
     * 预定投放时间（为空则立即执行）
     */
    private LocalDateTime scheduledTime;

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
