package com.douplus.account.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.douplus.common.domain.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 抖音账号实体
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("douyin_account")
public class DouyinAccount extends BaseEntity {

    /**
     * 所属用户ID
     */
    private Long userId;

    /**
     * 抖音OpenID
     */
    private String openId;

    /**
     * 广告主ID
     */
    private String advertiserId;

    /**
     * 抖音UnionID
     */
    private String unionId;

    /**
     * 抖音昵称
     */
    private String nickname;

    /**
     * 抖音头像
     */
    private String avatar;

    /**
     * 粉丝数
     */
    private Integer fansCount;

    /**
     * 关注数
     */
    private Integer followingCount;

    /**
     * 获赞数
     */
    private Integer totalFavorited;

    /**
     * AccessToken（AES加密）
     */
    private String accessToken;

    /**
     * RefreshToken（AES加密）
     */
    private String refreshToken;

    /**
     * Token过期时间
     */
    private LocalDateTime tokenExpiresAt;

    /**
     * 状态：0-授权失效，1-正常
     */
    private Integer status;

    /**
     * 单日投放限额
     */
    private BigDecimal dailyLimit;

    /**
     * 账户余额
     */
    private BigDecimal balance;

    /**
     * 备注
     */
    private String remark;
}