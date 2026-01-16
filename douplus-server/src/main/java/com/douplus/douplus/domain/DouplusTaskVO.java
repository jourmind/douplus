package com.douplus.douplus.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 投放任务VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DouplusTaskVO {

    private Long id;
    private Long accountId;
    private String accountNickname;
    private String accountAvatar;
    private String itemId;
    private String videoTitle;
    private String videoCoverUrl;
    private Integer taskType;
    private Integer targetType;
    private Integer duration;
    private BigDecimal budget;
    private BigDecimal actualCost;
    private Integer expectedExposure;
    private Integer actualExposure;
    private String status;
    private String statusText;
    private String orderId;
    private Integer retryCount;
    private String errorMsg;
    private LocalDateTime scheduledTime;
    private LocalDateTime executedTime;
    private LocalDateTime completedTime;
    private LocalDateTime createTime;

    /**
     * 从实体转换
     */
    public static DouplusTaskVO fromEntity(DouplusTask task) {
        if (task == null) {
            return null;
        }
        return DouplusTaskVO.builder()
                .id(task.getId())
                .accountId(task.getAccountId())
                .itemId(task.getItemId())
                .taskType(task.getTaskType())
                .targetType(task.getTargetType())
                .duration(task.getDuration())
                .budget(task.getBudget())
                .actualCost(task.getActualCost())
                .expectedExposure(task.getExpectedExposure())
                .actualExposure(task.getActualExposure())
                .status(task.getStatus())
                .statusText(getStatusText(task.getStatus()))
                .orderId(task.getOrderId())
                .retryCount(task.getRetryCount())
                .errorMsg(task.getErrorMsg())
                .scheduledTime(task.getScheduledTime())
                .executedTime(task.getExecutedTime())
                .completedTime(task.getCompletedTime())
                .createTime(task.getCreateTime())
                .build();
    }

    private static String getStatusText(String status) {
        if (status == null) return "";
        return switch (status) {
            case "WAIT" -> "待执行";
            case "RUNNING" -> "执行中";
            case "SUCCESS" -> "已完成";
            case "FAIL" -> "失败";
            case "CANCELLED" -> "已取消";
            default -> status;
        };
    }
}
