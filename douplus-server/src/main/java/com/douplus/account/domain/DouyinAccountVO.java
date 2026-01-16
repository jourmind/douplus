package com.douplus.account.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 抖音账号VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DouyinAccountVO {

    private Long id;
    private String openId;
    private String nickname;
    private String avatar;
    private Integer fansCount;
    private Integer followingCount;
    private Integer totalFavorited;
    private Integer status;
    private BigDecimal dailyLimit;
    private BigDecimal balance;
    private String remark;
    private LocalDateTime tokenExpiresAt;
    private LocalDateTime createTime;

    /**
     * Token是否即将过期（7天内）
     */
    private Boolean tokenExpiringSoon;

    public static DouyinAccountVO fromEntity(DouyinAccount account) {
        if (account == null) {
            return null;
        }
        boolean expiringSoon = account.getTokenExpiresAt() != null && 
                account.getTokenExpiresAt().isBefore(LocalDateTime.now().plusDays(7));
        
        return DouyinAccountVO.builder()
                .id(account.getId())
                .openId(account.getOpenId())
                .nickname(account.getNickname())
                .avatar(account.getAvatar())
                .fansCount(account.getFansCount())
                .followingCount(account.getFollowingCount())
                .totalFavorited(account.getTotalFavorited())
                .status(account.getStatus())
                .dailyLimit(account.getDailyLimit())
                .balance(account.getBalance())
                .remark(account.getRemark())
                .tokenExpiresAt(account.getTokenExpiresAt())
                .createTime(account.getCreateTime())
                .tokenExpiringSoon(expiringSoon)
                .build();
    }
}
