package com.douplus.douplus.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.auth.service.SysUserService;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.ResultCode;
import com.douplus.douplus.client.DouyinAdClient;
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
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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
    private final DouyinAdClient douyinAdClient;

    @Value("${security.daily-limit:10000}")
    private BigDecimal systemDailyLimit;

    @Value("${security.max-single-amount:5000}")
    private BigDecimal maxSingleAmount;

    /**
     * 同步DOU+历史订单
     * 注意：不使用全局事务，每页独立提交，避免部分页面失败导致全部回滚
     */
    public int syncDouplusOrders(Long userId, Long accountId) {
        // 1. 验证账号归属
        DouyinAccount account = accountService.getByIdAndUserId(accountId, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        if (account.getStatus() != 1) {
            throw new BusinessException(ResultCode.ACCOUNT_TOKEN_EXPIRED);
        }

        // 2. 解密Token
        String accessToken;
        try {
            accessToken = new String(java.util.Base64.getDecoder().decode(account.getAccessToken()));
        } catch (Exception e) {
            log.error("解密Token失败", e);
            throw new BusinessException(ResultCode.ACCOUNT_TOKEN_EXPIRED, "Token解密失败");
        }

        // 3. 获取aweme_sec_uid（v3.0 API必需）
        String awemeSecUid = account.getAwemeSecUid();
        if (awemeSecUid == null || awemeSecUid.isEmpty()) {
            log.error("账号{}aweme_sec_uid为空，无法同步订单，请重新授权", accountId);
            throw new BusinessException(ResultCode.DOUPLUS_API_ERROR, 
                    "账号缺少aweme_sec_uid，请解除授权后重新授权该账号");
        }

        // 4. 分页获取所有订单（使用v3.0 API）
        int totalSynced = 0;
        int page = 1;
        int pageSize = 50;
        int errorCount = 0;
        final int MAX_ERRORS = 3; // 最大允许连续错误次数
        
        while (errorCount < MAX_ERRORS) {
            try {
                DouyinAdClient.DouplusOrderListResult result = 
                        douyinAdClient.getDouplusOrderListV3(accessToken, awemeSecUid, page, pageSize);
                
                if (result.getOrders() == null || result.getOrders().isEmpty()) {
                    log.info("第{}页无数据，同步完成", page);
                    break;
                }

                // 重置错误计数
                errorCount = 0;
                
                for (DouyinAdClient.DouplusOrderItem order : result.getOrders()) {
                    try {
                        // 检查订单是否已存在
                        DouplusTask existingTask = getOne(new LambdaQueryWrapper<DouplusTask>()
                                .eq(DouplusTask::getOrderId, order.getOrderId())
                                .eq(DouplusTask::getDeleted, 0));
                        
                        if (existingTask != null) {
                            // 更新现有订单的统计数据
                            updateOrderStats(existingTask, order);
                        } else {
                            // 创建新订单
                            createSyncedOrder(userId, accountId, order);
                            totalSynced++;
                        }
                    } catch (Exception e) {
                        log.warn("保存订单{}失败: {}", order.getOrderId(), e.getMessage());
                    }
                }
                
                log.info("同步第{}页完成，本页{}条，新增{}条", page, result.getOrders().size(), totalSynced);

                if (result.getOrders().size() < pageSize) {
                    log.info("最后一页，同步完成");
                    break;
                }
                page++;
                
                // 防止请求过快被限流
                try {
                    Thread.sleep(200);
                } catch (InterruptedException ignored) {}
                
            } catch (Exception e) {
                errorCount++;
                log.error("同步DOU+订单失败，页码: {}，错误次数: {}", page, errorCount, e);
                
                if (errorCount >= MAX_ERRORS) {
                    log.warn("连续错误{}次，停止同步，已同步{}条订单", MAX_ERRORS, totalSynced);
                    break;
                }
                
                // 等待一下再重试
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ignored) {}
            }
        }

        log.info("用户{}同步了{}个DOU+历史订单", userId, totalSynced);
        
        // 5. 同步完订单列表后，调用效果报告API获取统计数据
        log.info(">>> 准备调用效果报告API...");
        try {
            syncOrderStats(userId, accountId, accessToken, awemeSecUid);
            log.info(">>> 效果报告API调用完成");
        } catch (Exception e) {
            log.error(">>> 同步订单效果数据失败: {}", e.getMessage(), e);
        }
        
        return totalSynced;
    }

    /**
     * 同步订单效果统计数据
     * 调用DOU+订单效果报告API获取播放量、点赞量等统计数据
     */
    private void syncOrderStats(Long userId, Long accountId, String accessToken, String awemeSecUid) {
        log.info(">>> syncOrderStats开始: userId={}, accountId={}", userId, accountId);
        
        // 获取该账号所有订单（用于后续更新）
        List<DouplusTask> tasks = list(new LambdaQueryWrapper<DouplusTask>()
                .eq(DouplusTask::getUserId, userId)
                .eq(DouplusTask::getAccountId, accountId)
                .eq(DouplusTask::getDeleted, 0)
                .isNotNull(DouplusTask::getOrderId));
        
        log.info(">>> 查询到{}条订单需要同步效果数据", tasks.size());
        
        if (tasks.isEmpty()) {
            log.info("无订单需要同步效果数据");
            return;
        }
        
        // 构建订单ID -> Task的映射，方便后续查找
        Map<String, DouplusTask> taskMap = tasks.stream()
                .filter(t -> t.getOrderId() != null && !t.getOrderId().isEmpty())
                .collect(Collectors.toMap(DouplusTask::getOrderId, t -> t, (a, b) -> a));
        
        // 计算时间范围：最近90天（避免超限）
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        String beginTime = LocalDateTime.now().minusDays(90).format(formatter);
        String endTime = LocalDateTime.now().format(formatter);
        
        log.info("调用效果报告API，时间范围: {} ~ {}", beginTime, endTime);
        
        // 调用效果报告API（直接获取全部数据，API会分页返回）
        try {
            DouyinAdClient.DouplusOrderReportResult reportResult = 
                    douyinAdClient.getDouplusOrderReport(accessToken, awemeSecUid, null, beginTime, endTime);
            
            log.info(">>> API返回{}条效果数据", 
                    reportResult.getOrderStats() != null ? reportResult.getOrderStats().size() : 0);
            
            if (reportResult.getOrderStats() != null && !reportResult.getOrderStats().isEmpty()) {
                int updatedCount = 0;
                // 遍历API返回的效果数据，更新对应订单
                for (Map.Entry<String, DouyinAdClient.DouplusOrderStats> entry : reportResult.getOrderStats().entrySet()) {
                    String orderId = entry.getKey();
                    DouyinAdClient.DouplusOrderStats stats = entry.getValue();
                    
                    DouplusTask task = taskMap.get(orderId);
                    if (task != null) {
                        updateTaskWithStats(task, stats);
                        updatedCount++;
                    }
                }
                log.info(">>> 成功更新{}条订单的效果数据", updatedCount);
            } else {
                log.warn(">>> API返回的效果数据为空");
            }
            
        } catch (Exception e) {
            log.error("获取订单效果数据失败: {}", e.getMessage(), e);
        }
        
        log.info("订单效果数据同步完成");
    }

    /**
     * 更新订单统计数据
     */
    private void updateTaskWithStats(DouplusTask task, DouyinAdClient.DouplusOrderStats stats) {
        boolean updated = false;
        
        if (stats.getStatCost() != null && stats.getStatCost().compareTo(java.math.BigDecimal.ZERO) > 0) {
            task.setActualCost(stats.getStatCost());
            updated = true;
        }
        if (stats.getPlayCount() != null && stats.getPlayCount() > 0) {
            task.setPlayCount(stats.getPlayCount());
            task.setActualExposure(stats.getPlayCount());
            updated = true;
        }
        if (stats.getLikeCount() != null && stats.getLikeCount() > 0) {
            task.setLikeCount(stats.getLikeCount());
            updated = true;
        }
        if (stats.getCommentCount() != null && stats.getCommentCount() > 0) {
            task.setCommentCount(stats.getCommentCount());
            updated = true;
        }
        if (stats.getShareCount() != null && stats.getShareCount() > 0) {
            task.setShareCount(stats.getShareCount());
            updated = true;
        }
        if (stats.getFollowCount() != null && stats.getFollowCount() > 0) {
            task.setFollowCount(stats.getFollowCount());
            updated = true;
        }
        if (stats.getClickCount() != null && stats.getClickCount() > 0) {
            task.setClickCount(stats.getClickCount());
            updated = true;
        }
        
        if (updated) {
            updateById(task);
            log.debug("更新订单{}统计数据: 消耗={}, 播放={}, 点赞={}, 转发={}", 
                    task.getOrderId(), task.getActualCost(), task.getPlayCount(), task.getLikeCount(), task.getShareCount());
        }
    }

    /**
     * 更新订单统计数据
     */
    private void updateOrderStats(DouplusTask task, DouyinAdClient.DouplusOrderItem order) {
        task.setActualCost(order.getActualCost());
        task.setPlayCount(order.getPlayCount());
        task.setLikeCount(order.getLikeCount());
        task.setCommentCount(order.getCommentCount());
        task.setShareCount(order.getShareCount());
        task.setFollowCount(order.getFollowCount());
        task.setClickCount(order.getClickCount());
        task.setStatus(convertStatus(order.getStatus()));
        // 更新视频信息
        if (order.getAwemeTitle() != null) task.setVideoTitle(order.getAwemeTitle());
        if (order.getAwemeCover() != null) task.setVideoCoverUrl(order.getAwemeCover());
        updateById(task);
    }

    /**
     * 创建同步的订单
     */
    private void createSyncedOrder(Long userId, Long accountId, DouyinAdClient.DouplusOrderItem order) {
        DouplusTask task = new DouplusTask();
        task.setUserId(userId);
        task.setAccountId(accountId);
        task.setItemId(order.getAwemeId());
        task.setOrderId(order.getOrderId());
        task.setTaskType(1);
        task.setTargetType(1);
        task.setDuration(order.getDuration() != null ? order.getDuration() : 24);
        task.setBudget(order.getBudget());
        task.setActualCost(order.getActualCost());
        task.setActualExposure(order.getPlayCount());
        task.setPlayCount(order.getPlayCount());
        task.setLikeCount(order.getLikeCount());
        task.setCommentCount(order.getCommentCount());
        task.setShareCount(order.getShareCount());
        task.setFollowCount(order.getFollowCount());
        task.setClickCount(order.getClickCount());
        task.setSource("synced");
        task.setAwemeNick(order.getAwemeNick());
        task.setAwemeAvatar(order.getAwemeAvatar());
        task.setVideoTitle(order.getAwemeTitle());
        task.setVideoCoverUrl(order.getAwemeCover());
        task.setStatus(convertStatus(order.getStatus()));
        task.setRetryCount(0);
        task.setMaxRetry(0);
        
        // 解析时间
        if (order.getCreateTime() != null && !order.getCreateTime().isEmpty()) {
            try {
                task.setScheduledTime(LocalDateTime.parse(order.getCreateTime().replace(" ", "T")));
                task.setCreateTime(task.getScheduledTime());
            } catch (Exception e) {
                task.setScheduledTime(LocalDateTime.now());
            }
        }
        if (order.getStartTime() != null && !order.getStartTime().isEmpty()) {
            try {
                task.setExecutedTime(LocalDateTime.parse(order.getStartTime().replace(" ", "T")));
            } catch (Exception ignored) {}
        }
        if (order.getEndTime() != null && !order.getEndTime().isEmpty()) {
            try {
                task.setCompletedTime(LocalDateTime.parse(order.getEndTime().replace(" ", "T")));
            } catch (Exception ignored) {}
        }
        
        save(task);
    }

    /**
     * 转换订单状态 - DOU+官方状态到系统状态
     * DOU+官方状态：
     * - UNPAID: 未支付
     * - AUDITING: 审核中
     * - DELIVERING: 投放中
     * - FINISHED/COMPLETE: 投放完成/结束
     * - TERMINATED/STOPPED: 投放终止
     * - AUDIT_PAUSE: 审核暂停
     * - AUDIT_REJECTED/REJECTED: 审核不通过
     */
    private String convertStatus(String apiStatus) {
        if (apiStatus == null) return "FINISHED";
        String status = apiStatus.toUpperCase().trim();
        
        // 直接保存原始状态，让前端映射显示
        return switch (status) {
            // 未支付
            case "UNPAID", "NOT_PAY" -> "UNPAID";
            // 审核中
            case "AUDITING", "AUDIT", "REVIEWING" -> "AUDITING";
            // 投放中
            case "DELIVERING", "RUNNING", "ACTIVE" -> "DELIVERING";
            // 投放完成
            case "FINISHED", "COMPLETE", "COMPLETED", "SUCCESS", "DONE" -> "FINISHED";
            // 投放终止
            case "TERMINATED", "STOPPED", "STOP", "CANCELLED", "CANCELED" -> "TERMINATED";
            // 审核暂停
            case "AUDIT_PAUSE", "PAUSED", "PAUSE" -> "AUDIT_PAUSE";
            // 审核不通过
            case "AUDIT_REJECTED", "REJECTED", "FAILED", "FAIL" -> "AUDIT_REJECTED";
            // 其他状态保持原样
            default -> status;
        };
    }

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
            task.setTargetAccountId(request.getTargetAccountId());
            task.setItemId(request.getItemId());
            task.setTaskType(request.getTaskType() != null ? request.getTaskType() : 1);
            task.setTargetType(request.getTargetType() != null ? request.getTargetType() : 1);
            task.setWantType(request.getWantType() != null ? request.getWantType() : "CONTENT_HEAT");
            task.setObjective(request.getObjective() != null ? request.getObjective() : "LIKE_COMMENT");
            task.setStrategy(request.getStrategy() != null ? request.getStrategy() : "GUARANTEE_PLAY");
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
     * 批量创建多个不同任务
     */
    @Transactional(rollbackFor = Exception.class)
    public List<DouplusTask> createMultipleTasks(Long userId, List<CreateTaskRequest> requests) {
        List<DouplusTask> allTasks = new ArrayList<>();
        
        for (CreateTaskRequest request : requests) {
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

            // 3. 风控检查（针对单个任务）
            validateSingleTaskRiskControl(userId, account, request);

            // 4. 创建任务（支持投放笔数）
            int taskCount = request.getCount() != null ? request.getCount() : 1;
            for (int i = 0; i < taskCount; i++) {
                DouplusTask task = new DouplusTask();
                task.setUserId(userId);
                task.setAccountId(request.getAccountId());
                task.setTargetAccountId(request.getTargetAccountId());
                task.setItemId(request.getItemId());
                task.setTaskType(request.getTaskType() != null ? request.getTaskType() : 1);
                task.setTargetType(request.getTargetType() != null ? request.getTargetType() : 1);
                task.setWantType(request.getWantType() != null ? request.getWantType() : "CONTENT_HEAT");
                task.setObjective(request.getObjective() != null ? request.getObjective() : "LIKE_COMMENT");
                task.setStrategy(request.getStrategy() != null ? request.getStrategy() : "GUARANTEE_PLAY");
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
                allTasks.add(task);
            }
            
        }

        log.info("用户{}批量创建了{}个投放任务", userId, allTasks.size());
        
        return allTasks;
    }

    /**
     * 对单个任务进行风控检查
     */
    private void validateSingleTaskRiskControl(Long userId, DouyinAccount account, CreateTaskRequest request) {
        BigDecimal budget = request.getBudget();

        // 1. 检查单笔金额上限
        if (budget.compareTo(maxSingleAmount) > 0) {
            throw new BusinessException(ResultCode.BUDGET_EXCEED_LIMIT, 
                    "单笔投放金额不能超过" + maxSingleAmount + "元");
        }

        // 2. 检查账号单日限额
        BigDecimal dailyUsed = baseMapper.sumDailyBudget(account.getId(), LocalDate.now());
        BigDecimal accountDailyLimit = account.getDailyLimit() != null ? 
                account.getDailyLimit() : systemDailyLimit;
        
        if (dailyUsed.add(budget).compareTo(accountDailyLimit) > 0) {
            throw new BusinessException(ResultCode.DAILY_LIMIT_EXCEED, 
                    "账号今日投放已达限额，当前已用：" + dailyUsed + "元，限额：" + accountDailyLimit + "元");
        }

        // 3. 检查用户总限额
        BigDecimal userDailyUsed = baseMapper.sumUserDailyBudget(userId, LocalDate.now());
        if (userDailyUsed.add(budget).compareTo(systemDailyLimit) > 0) {
            throw new BusinessException(ResultCode.DAILY_LIMIT_EXCEED, 
                    "今日投放已达系统限额，当前已用：" + userDailyUsed + "元");
        }
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
