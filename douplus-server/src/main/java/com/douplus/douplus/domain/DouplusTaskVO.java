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
    private Integer playCount;
    private Integer likeCount;
    private Integer commentCount;
    private Integer shareCount;
    private Integer followCount;
    private Integer clickCount;
    private String source;
    private String awemeNick;
    private String awemeAvatar;
    private String status;
    private String statusText;
    private String orderId;
    private Integer retryCount;
    private String errorMsg;
    private LocalDateTime scheduledTime;
    private LocalDateTime executedTime;
    private LocalDateTime completedTime;
    private LocalDateTime orderEndTime;  // 订单结束时间 = 生效时间 + 投放时长
    private LocalDateTime createTime;

    /**
     * 从实体转换
     */
    public static DouplusTaskVO fromEntity(DouplusTask task) {
        if (task == null) {
            return null;
        }
        
        // 计算订单结束时间 = 生效时间(executedTime) + 投放时长(duration小时)
        LocalDateTime orderEndTime = null;
        if (task.getExecutedTime() != null && task.getDuration() != null) {
            orderEndTime = task.getExecutedTime().plusHours(task.getDuration());
        } else if (task.getScheduledTime() != null && task.getDuration() != null) {
            // 如果还未执行，用计划时间估算
            orderEndTime = task.getScheduledTime().plusHours(task.getDuration());
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
                .playCount(task.getPlayCount())
                .likeCount(task.getLikeCount())
                .commentCount(task.getCommentCount())
                .shareCount(task.getShareCount())
                .followCount(task.getFollowCount())
                .clickCount(task.getClickCount())
                .source(task.getSource())
                .awemeNick(task.getAwemeNick())
                .awemeAvatar(task.getAwemeAvatar())
                .videoTitle(task.getVideoTitle())
                .videoCoverUrl(task.getVideoCoverUrl())
                .status(task.getStatus())
                .statusText(getStatusText(task.getStatus()))
                .orderId(task.getOrderId())
                .retryCount(task.getRetryCount())
                .errorMsg(task.getErrorMsg())
                .scheduledTime(task.getScheduledTime())
                .executedTime(task.getExecutedTime())
                .completedTime(task.getCompletedTime())
                .orderEndTime(orderEndTime)
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
