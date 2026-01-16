package com.douplus.douplus.task;

import com.douplus.account.service.DouyinAccountService;
import com.douplus.douplus.client.DouyinAdClient;
import com.douplus.douplus.domain.DouplusTask;
import com.douplus.douplus.service.DouplusTaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * DOU+投放任务执行器
 * 
 * 核心设计：
 * 1. 定时扫描待执行任务
 * 2. 调用抖音API执行投放
 * 3. 失败自动重试
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DouplusTaskExecutor {

    private final DouplusTaskService taskService;
    private final DouyinAccountService accountService;
    private final DouyinAdClient adClient;

    /**
     * 定时执行投放任务（每5秒检查一次）
     */
    @Scheduled(fixedDelay = 5000)
    public void executeTask() {
        // 1. 查询待执行任务
        List<DouplusTask> pendingTasks = taskService.listPendingTasks();
        
        if (pendingTasks.isEmpty()) {
            return;
        }
        
        log.info("发现{}个待执行投放任务", pendingTasks.size());
        
        for (DouplusTask task : pendingTasks) {
            try {
                executeOne(task);
            } catch (Exception e) {
                log.error("执行任务{}失败", task.getId(), e);
                taskService.markFailed(task.getId(), e.getMessage());
            }
        }
    }

    /**
     * 执行单个任务
     */
    private void executeOne(DouplusTask task) {
        log.info("开始执行投放任务: id={}, itemId={}, budget={}", 
                task.getId(), task.getItemId(), task.getBudget());
        
        // 1. 标记为执行中
        taskService.markRunning(task.getId());
        
        try {
            // 2. 获取AccessToken
            String accessToken = accountService.getDecryptedAccessToken(task.getAccountId());
            
            // 3. 构建请求
            DouyinAdClient.CreateOrderRequest request = new DouyinAdClient.CreateOrderRequest();
            request.setItemId(task.getItemId());
            request.setBudget(task.getBudget());
            request.setDuration(task.getDuration());
            request.setTargetType(task.getTargetType());
            request.setTargetConfig(task.getTargetConfig());
            
            // 4. 调用抖音API创建订单
            DouyinAdClient.CreateOrderResult result = adClient.createOrder(accessToken, request);
            
            // 5. 更新任务状态为成功
            taskService.markSuccess(task.getId(), result.getOrderId(), result.getExpectedExposure());
            
            log.info("投放任务执行成功: id={}, orderId={}", task.getId(), result.getOrderId());
            
        } catch (Exception e) {
            log.error("投放任务执行失败: id={}, error={}", task.getId(), e.getMessage());
            taskService.markFailed(task.getId(), e.getMessage());
        }
    }
}
