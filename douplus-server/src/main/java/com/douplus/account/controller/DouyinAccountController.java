package com.douplus.account.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.domain.DouyinAccountVO;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.account.task.TokenRefreshTask;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.common.result.ResultCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;

/**
 * 抖音账号管理Controller
 */
@Slf4j
@RestController
@RequestMapping("/account")
@RequiredArgsConstructor
public class DouyinAccountController {

    private final DouyinAccountService accountService;
    private final TokenRefreshTask tokenRefreshTask;

    @Value("${douyin.api.app-id:}")
    private String appId;

    @Value("${douyin.api.oauth-callback:}")
    private String oauthCallback;

    @Value("${douyin.api.oauth-url:https://open.oceanengine.com/audit/oauth.html}")
    private String oauthBaseUrl;

    /**
     * 获取账号列表
     */
    @GetMapping("/list")
    public R<List<DouyinAccountVO>> list() {
        Long userId = SecurityUtils.getCurrentUserId();
        List<DouyinAccountVO> accounts = accountService.listByUserId(userId);
        return R.ok(accounts);
    }

    /**
     * 分页查询账号
     */
    @GetMapping("/page")
    public R<Page<DouyinAccountVO>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        Page<DouyinAccountVO> page = accountService.pageByUserId(userId, pageNum, pageSize);
        return R.ok(page);
    }

    /**
     * 获取账号详情
     */
    @GetMapping("/{id}")
    public R<DouyinAccountVO> getById(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(id, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        return R.ok(DouyinAccountVO.fromEntity(account));
    }

    /**
     * 更新账号备注
     */
    @PutMapping("/{id}/remark")
    public R<Void> updateRemark(@PathVariable Long id, @RequestBody UpdateRemarkRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(id, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        account.setRemark(request.getRemark());
        accountService.updateById(account);
        return R.ok(null, "备注更新成功");
    }

    /**
     * 更新单日投放限额
     */
    @PutMapping("/{id}/daily-limit")
    public R<Void> updateDailyLimit(@PathVariable Long id, @RequestBody UpdateDailyLimitRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(id, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        accountService.updateDailyLimit(id, request.getDailyLimit());
        return R.ok(null, "限额更新成功");
    }

    /**
     * 删除账号（解绑）
     */
    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(id, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        accountService.removeById(id);
        log.info("用户{}解绑抖音账号: {}", userId, account.getNickname());
        return R.ok(null, "账号解绑成功");
    }

    /**
     * 手动刷新Token
     */
    @PostMapping("/{id}/refresh-token")
    public R<Void> refreshToken(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(id, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        boolean success = tokenRefreshTask.manualRefresh(id);
        if (success) {
            return R.ok(null, "Token刷新成功");
        } else {
            throw new BusinessException("刷新失败，请检查账号状态或重新授权");
        }
    }

    /**
     * 获取OAuth授权URL
     */
    @GetMapping("/oauth/url")
    public R<String> getOAuthUrl() {
        if (appId == null || appId.isEmpty()) {
            throw new BusinessException("抖音应用未配置，请先配置APP_ID");
        }
        
        // 生成随机state防止CSRF攻击
        String state = UUID.randomUUID().toString().replace("-", "").substring(0, 16);
        Long userId = SecurityUtils.getCurrentUserId();
        
        // 构建授权URL（巨量营销DOU+授权）
        StringBuilder urlBuilder = new StringBuilder(oauthBaseUrl);
        urlBuilder.append("?app_id=").append(appId);
        urlBuilder.append("&state=").append(userId).append("_").append(state);
        urlBuilder.append("&material_auth=1");
        urlBuilder.append("&rid=vc6i9tazan");  // 巨量营销必须参数
        
        // 如果配置了回调地址，添加redirect_uri参数
        if (oauthCallback != null && !oauthCallback.isEmpty()) {
            urlBuilder.append("&redirect_uri=").append(URLEncoder.encode(oauthCallback, StandardCharsets.UTF_8));
        }
        
        String oauthUrl = urlBuilder.toString();
        log.info("生成OAuth授权URL: {}", oauthUrl);
        return R.ok(oauthUrl);
    }

    // ======== 内部请求类 ========

    @lombok.Data
    static class UpdateRemarkRequest {
        private String remark;
    }

    @lombok.Data
    static class UpdateDailyLimitRequest {
        private BigDecimal dailyLimit;
    }
}
