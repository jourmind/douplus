package com.douplus.comment.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.douplus.common.domain.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 敏感词/黑名单
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("keyword_blacklist")
public class KeywordBlacklist extends BaseEntity {

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 关键词
     */
    private String keyword;

    /**
     * 类型：1-敏感词，2-用户黑名单
     */
    private Integer type;

    /**
     * 是否自动删除
     */
    private Integer autoDelete;

    // 类型常量
    public static final int TYPE_KEYWORD = 1;
    public static final int TYPE_USER = 2;
}
