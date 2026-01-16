package com.douplus.douplus.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.auth.service.SysUserService;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.ResultCode;
import com.douplus.douplus.domain.CreateTaskRequest;
import com.douplus.douplus.domain.DouplusTask;
import com.douplus.douplus.domain.DouplusTaskVO;
import com.douplus.douplus.mapper.DouplusTaskMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * DOU+投放任务Service
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DouplusTaskService extends ServiceImpl<DouplusTaskMapper, DouplusTask> {

    private final DouyinAccountService accountService;
    private final SysUserService userService;

    @Value("${security.daily-limit:10000}")
    private BigDecimal systemDailyLimit;

    @Value("${security.max-single-amount:5000}")
    private BigDecimal maxSingleAmount;

    /**
     * 创建投放任务
     */
    @Transactional(rollbackFor = Exception.class)
    public List<DouplusTask> createTasks(Long userId, CreateTaskRequest request) {
        // 1. 验证投放密码
        if (!userService.validateInvestPassword(userId, request.getInvestPassword())) {
            throw new BusinessException(ResultCode.INVEST_PASSWORD_ERROR);
        }

        // 2. 验证账号归属
        DouyinAccount account = accountService.getByIdAndUserId(request.getAccountId(), userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        if (account.getStatus() != 1) {
            throw new BusinessException(ResultCode.ACCOUNT_TOKEN_EXPIRED);
        }

        // 3. 风控检查
        validateRiskControl(userId, account, request);

        // 4. 创建任务
        List<DouplusTask> tasks = new ArrayList<>();
        int count = request.getCount() != null ? request.getCount() : 1;
        
        for (int i = 0; i < count; i++) {
            DouplusTask task = new DouplusTask();
            task.setUserId(userId);
            task.setAccountId(request.getAccountId());
            task.setItemId(request.getItemId());
            task.setTaskType(request.getTaskType() != null ? request.getTaskType() : 1);
            task.setTargetType(request.getTargetType() != null ? request.getTargetType() : 1);
            task.setDuration(request.getDuration() != null ? request.getDuration() : 24);
            task.setBudget(request.getBudget());
            task.setActualCost(BigDecimal.ZERO);
            task.setExpectedExposure(0);
            task.setActualExposure(0);
            task.setStatus(DouplusTask.STATUS_WAIT);
            task.setRetryCount(0);
            task.setMaxRetry(3);
            task.setScheduledTime(request.getScheduledTime() != null ? 
                    request.getScheduledTime() : LocalDateTime.now());
            task.setTargetConfig(request.getTargetConfig());
            
            save(task);
            tasks.add(task);
        }

        log.info("用户{}创建了{}个投放任务，账号：{}，视频：{}，单笔金额：{}", 
                userId, count, account.getNickname(), request.getItemId(), request.getBudget());
        
        return tasks;
    }

    /**
     * 风控检查
     */
    private void validateRiskControl(Long userId, DouyinAccount account, CreateTaskRequest request) {
        BigDecimal budget = request.getBudget();
        int count = request.getCount() != null ? request.getCount() : 1;
        BigDecimal totalBudget = budget.multiply(BigDecimal.valueOf(count));

        // 1. 检查单笔金额上限
        if (budget.compareTo(maxSingleAmount) > 0) {
            throw new BusinessException(ResultCode.BUDGET_EXCEED_LIMIT, 
                    "单笔投放金额不能超过" + maxSingleAmount + "元");
        }

        // 2. 检查账号单日限额
        BigDecimal dailyUsed = baseMapper.sumDailyBudget(account.getId(), LocalDate.now());
        BigDecimal accountDailyLimit = account.getDailyLimit() != null ? 
                account.getDailyLimit() : systemDailyLimit;
        
        if (dailyUsed.add(totalBudget).compareTo(accountDailyLimit) > 0) {
            throw new BusinessException(ResultCode.DAILY_LIMIT_EXCEED, 
                    "账号今日投放已达限额，当前已用：" + dailyUsed + "元，限额：" + accountDailyLimit + "元");
        }

        // 3. 检查用户总限额
        BigDecimal userDailyUsed = baseMapper.sumUserDailyBudget(userId, LocalDate.now());
        if (userDailyUsed.add(totalBudget).compareTo(systemDailyLimit) > 0) {
            throw new BusinessException(ResultCode.DAILY_LIMIT_EXCEED, 
                    "今日投放已达系统限额，当前已用：" + userDailyUsed + "元");
        }

        // 4. TODO: 更多风控规则（余额检查等）
    }

    /**
     * 分页查询任务
     */
    public Page<DouplusTaskVO> pageByUserId(Long userId, Integer pageNum, Integer pageSize, String status) {
        LambdaQueryWrapper<DouplusTask> wrapper = new LambdaQueryWrapper<DouplusTask>()
                .eq(DouplusTask::getUserId, userId)
                .eq(DouplusTask::getDeleted, 0)
                .orderByDesc(DouplusTask::getCreateTime);
        
        if (status != null && !status.isEmpty()) {
            wrapper.eq(DouplusTask::getStatus, status);
        }
        
        Page<DouplusTask> page = page(new Page<>(pageNum, pageSize), wrapper);
        
        Page<DouplusTaskVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), page.getTotal());
        resultPage.setRecords(page.getRecords().stream()
                .map(this::toVO)
                .collect(Collectors.toList()));
        return resultPage;
    }

    /**
     * 查询待执行任务
     */
    public List<DouplusTask> listPendingTasks() {
        return list(new LambdaQueryWrapper<DouplusTask>()
                .eq(DouplusTask::getStatus, DouplusTask.STATUS_WAIT)
                .le(DouplusTask::getScheduledTime, LocalDateTime.now())
                .eq(DouplusTask::getDeleted, 0)
                .orderByAsc(DouplusTask::getScheduledTime)
                .last("LIMIT 10"));
    }

    /**
     * 取消任务
     */
    public void cancelTask(Long userId, Long taskId) {
        DouplusTask task = getById(taskId);
        if (task == null || !task.getUserId().equals(userId)) {
            throw new BusinessException(ResultCode.TASK_NOT_FOUND);
        }
        if (!DouplusTask.STATUS_WAIT.equals(task.getStatus())) {
            throw new BusinessException(ResultCode.TASK_STATUS_ERROR, "只能取消待执行的任务");
        }
        task.setStatus(DouplusTask.STATUS_CANCELLED);
        updateById(task);
        log.info("用户{}取消了任务{}", userId, taskId);
    }

    /**
     * 更新任务状态为执行中
     */
    public void markRunning(Long taskId) {
        DouplusTask task = getById(taskId);
        if (task != null) {
            task.setStatus(DouplusTask.STATUS_RUNNING);
            task.setExecutedTime(LocalDateTime.now());
            updateById(task);
        }
    }

    /**
     * 更新任务为成功
     */
    public void markSuccess(Long taskId, String orderId, Integer exposure) {
        DouplusTask task = getById(taskId);
        if (task != null) {
            task.setStatus(DouplusTask.STATUS_SUCCESS);
            task.setOrderId(orderId);
            task.setActualExposure(exposure);
            task.setCompletedTime(LocalDateTime.now());
            updateById(task);
        }
    }

    /**
     * 更新任务为失败
     */
    public void markFailed(Long taskId, String errorMsg) {
        DouplusTask task = getById(taskId);
        if (task != null) {
            task.setRetryCount(task.getRetryCount() + 1);
            if (task.getRetryCount() >= task.getMaxRetry()) {
                task.setStatus(DouplusTask.STATUS_FAIL);
                task.setCompletedTime(LocalDateTime.now());
            } else {
                task.setStatus(DouplusTask.STATUS_WAIT); // 重新等待执行
            }
            task.setErrorMsg(errorMsg);
            updateById(task);
        }
    }

    /**
     * 转换为VO
     */
    private DouplusTaskVO toVO(DouplusTask task) {
        DouplusTaskVO vo = DouplusTaskVO.fromEntity(task);
        // 补充账号信息
        DouyinAccount account = accountService.getById(task.getAccountId());
        if (account != null) {
            vo.setAccountNickname(account.getNickname());
            vo.setAccountAvatar(account.getAvatar());
        }
        return vo;
    }
}
