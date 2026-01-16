package com.douplus.account.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.domain.DouyinAccountVO;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.common.result.ResultCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;

/**
 * 抖音账号管理Controller
 */
@Slf4j
@RestController
@RequestMapping("/account")
@RequiredArgsConstructor
public class DouyinAccountController {

    private final DouyinAccountService accountService;

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
     * 获取OAuth授权URL
     */
    @GetMapping("/oauth/url")
    public R<String> getOAuthUrl() {
        // TODO: 调用抖音API生成授权URL
        String oauthUrl = "https://open.douyin.com/platform/oauth/connect?client_key=xxx&response_type=code&scope=xxx&redirect_uri=xxx";
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
