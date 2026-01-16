package com.douplus.comment.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.douplus.common.domain.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;

/**
 * 评论实体
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("douyin_comment")
public class DouyinComment extends BaseEntity {

    /**
     * 账号ID
     */
    private Long accountId;

    /**
     * 视频ID
     */
    private Long videoId;

    /**
     * 抖音视频ID
     */
    private String itemId;

    /**
     * 抖音评论ID
     */
    private String commentId;

    /**
     * 评论内容
     */
    private String content;

    /**
     * 评论者昵称
     */
    private String nickname;

    /**
     * 评论者头像
     */
    private String avatar;

    /**
     * 点赞数
     */
    private Integer likeCount;

    /**
     * 回复数
     */
    private Integer replyCount;

    /**
     * 是否置顶
     */
    private Integer isTop;

    /**
     * 状态：0-已删除，1-正常，2-待删除
     */
    private Integer status;

    /**
     * 是否负面评论
     */
    private Integer isNegative;

    /**
     * 命中的关键词
     */
    private String keywordHit;

    /**
     * 评论时间
     */
    private LocalDateTime commentTime;

    // 状态常量
    public static final int STATUS_DELETED = 0;
    public static final int STATUS_NORMAL = 1;
    public static final int STATUS_PENDING_DELETE = 2;
}
