package com.douplus.account.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.domain.DouyinAccountVO;
import com.douplus.account.mapper.DouyinAccountMapper;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.ResultCode;
import com.douplus.common.utils.AesUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 抖音账号Service
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DouyinAccountService extends ServiceImpl<DouyinAccountMapper, DouyinAccount> {

    /**
     * 查询用户的账号列表
     */
    public List<DouyinAccountVO> listByUserId(Long userId) {
        List<DouyinAccount> accounts = list(new LambdaQueryWrapper<DouyinAccount>()
                .eq(DouyinAccount::getUserId, userId)
                .eq(DouyinAccount::getDeleted, 0)
                .orderByDesc(DouyinAccount::getCreateTime));
        return accounts.stream()
                .map(DouyinAccountVO::fromEntity)
                .collect(Collectors.toList());
    }

    /**
     * 分页查询账号
     */
    public Page<DouyinAccountVO> pageByUserId(Long userId, Integer pageNum, Integer pageSize) {
        Page<DouyinAccount> page = page(new Page<>(pageNum, pageSize),
                new LambdaQueryWrapper<DouyinAccount>()
                        .eq(DouyinAccount::getUserId, userId)
                        .eq(DouyinAccount::getDeleted, 0)
                        .orderByDesc(DouyinAccount::getCreateTime));
        
        Page<DouyinAccountVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), page.getTotal());
        resultPage.setRecords(page.getRecords().stream()
                .map(DouyinAccountVO::fromEntity)
                .collect(Collectors.toList()));
        return resultPage;
    }

    /**
     * 根据OpenID查询账号
     */
    public DouyinAccount getByOpenId(String openId) {
        return getOne(new LambdaQueryWrapper<DouyinAccount>()
                .eq(DouyinAccount::getOpenId, openId)
                .eq(DouyinAccount::getDeleted, 0));
    }

    /**
     * 创建或更新账号（OAuth回调时使用）
     */
    public DouyinAccount saveOrUpdateAccount(Long userId, String openId, String unionId, String nickname, 
                                              String avatar, String accessToken, String refreshToken, 
                                              LocalDateTime tokenExpiresAt) {
        DouyinAccount account = getByOpenId(openId);
        
        if (account == null) {
            // 新建账号
            account = new DouyinAccount();
            account.setUserId(userId);
            account.setOpenId(openId);
            account.setUnionId(unionId);
            account.setDailyLimit(new BigDecimal("10000"));
            account.setBalance(BigDecimal.ZERO);
        }
        
        account.setNickname(nickname);
        account.setAvatar(avatar);
        account.setAccessToken(AesUtils.encrypt(accessToken));
        account.setRefreshToken(AesUtils.encrypt(refreshToken));
        account.setTokenExpiresAt(tokenExpiresAt);
        account.setStatus(1);
        
        saveOrUpdate(account);
        return account;
    }

    /**
     * 获取解密后的AccessToken
     */
    public String getDecryptedAccessToken(Long accountId) {
        DouyinAccount account = getById(accountId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        if (account.getStatus() != 1) {
            throw new BusinessException(ResultCode.ACCOUNT_TOKEN_EXPIRED);
        }
        return AesUtils.decrypt(account.getAccessToken());
    }

    /**
     * 刷新Token
     */
    public void refreshToken(Long accountId, String newAccessToken, String newRefreshToken, 
                            LocalDateTime newExpiresAt) {
        DouyinAccount account = getById(accountId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        account.setAccessToken(AesUtils.encrypt(newAccessToken));
        account.setRefreshToken(AesUtils.encrypt(newRefreshToken));
        account.setTokenExpiresAt(newExpiresAt);
        account.setStatus(1);
        updateById(account);
    }

    /**
     * 设置授权失效
     */
    public void setTokenExpired(Long accountId) {
        DouyinAccount account = getById(accountId);
        if (account != null) {
            account.setStatus(0);
            updateById(account);
        }
    }

    /**
     * 更新账号信息
     */
    public void updateAccountInfo(Long accountId, Integer fansCount, Integer followingCount, 
                                  Integer totalFavorited, BigDecimal balance) {
        DouyinAccount account = getById(accountId);
        if (account != null) {
            if (fansCount != null) account.setFansCount(fansCount);
            if (followingCount != null) account.setFollowingCount(followingCount);
            if (totalFavorited != null) account.setTotalFavorited(totalFavorited);
            if (balance != null) account.setBalance(balance);
            updateById(account);
        }
    }

    /**
     * 更新单日限额
     */
    public void updateDailyLimit(Long accountId, BigDecimal dailyLimit) {
        DouyinAccount account = getById(accountId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        account.setDailyLimit(dailyLimit);
        updateById(account);
    }

    /**
     * 验证账号归属
     */
    public DouyinAccount getByIdAndUserId(Long accountId, Long userId) {
        return getOne(new LambdaQueryWrapper<DouyinAccount>()
                .eq(DouyinAccount::getId, accountId)
                .eq(DouyinAccount::getUserId, userId)
                .eq(DouyinAccount::getDeleted, 0));
    }

    /**
     * 查询即将过期的账号（用于定时刷新）
     */
    public List<DouyinAccount> listExpiringAccounts() {
        LocalDateTime expirationThreshold = LocalDateTime.now().plusDays(7);
        return list(new LambdaQueryWrapper<DouyinAccount>()
                .eq(DouyinAccount::getStatus, 1)
                .eq(DouyinAccount::getDeleted, 0)
                .lt(DouyinAccount::getTokenExpiresAt, expirationThreshold));
    }
}
