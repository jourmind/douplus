package com.douplus.douplus.controller;

import com.douplus.account.service.DouyinAccountService;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.douplus.domain.CreateTaskRequest;
import com.douplus.douplus.service.DouplusTaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * DOU+投放任务Controller
 */
@Slf4j
@RestController
@RequestMapping("/douplus/task")
@RequiredArgsConstructor
public class DouplusTaskController {

    private final DouplusTaskService taskService;
    private final DouyinAccountService accountService;
    
    // 同步状态存储：userId -> {status, count, message}
    private static final Map<Long, Map<String, Object>> syncStatusMap = new ConcurrentHashMap<>();
    private static final ExecutorService syncExecutor = Executors.newFixedThreadPool(2);

    /**
     * 创建投放任务（支持单个或批量）
     */
    @PostMapping("/create")
    public R<List<com.douplus.douplus.domain.DouplusTask>> createTask(@RequestBody List<CreateTaskRequest> requests) {
        if (requests == null || requests.isEmpty()) {
            throw new IllegalArgumentException("投放任务不能为空");
        }
        
        Long userId = SecurityUtils.getCurrentUserId();
        List<com.douplus.douplus.domain.DouplusTask> tasks = taskService.createMultipleTasks(userId, requests);
        
        log.info("用户{}创建了{}个投放任务", userId, tasks.size());
        return R.ok(tasks, "投放任务创建成功，共" + tasks.size() + "个任务");
    }

    /**
     * 创建单个投放任务（兼容旧版）
     */
    @PostMapping("/create-single")
    public R<com.douplus.douplus.domain.DouplusTask> createSingleTask(@RequestBody CreateTaskRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        List<com.douplus.douplus.domain.DouplusTask> tasks = taskService.createTasks(userId, request);
        com.douplus.douplus.domain.DouplusTask task = tasks.isEmpty() ? null : tasks.get(0);
        
        log.info("用户{}创建了投放任务: {}", userId, task != null ? task.getId() : "null");
        return R.ok(task, "投放任务创建成功");
    }

    /**
     * 分页查询投放记录
     */
    @GetMapping("/page")
    public R<?> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) Long accountId,
            @RequestParam(required = false, defaultValue = "createTime") String sortField,
            @RequestParam(required = false, defaultValue = "desc") String sortOrder) {
        Long userId = SecurityUtils.getCurrentUserId();
        var result = taskService.pageByUserId(userId, pageNum, pageSize, status, accountId, sortField, sortOrder);
        return R.ok(result);
    }

    /**
     * 获取指定账号的订单统计数据
     */
    @GetMapping("/stats/{accountId}")
    public R<?> getAccountStats(@PathVariable Long accountId) {
        Long userId = SecurityUtils.getCurrentUserId();
        var stats = taskService.getAccountStats(userId, accountId);
        return R.ok(stats);
    }

    /**
     * 获取任务详情
     */
    @GetMapping("/{id}")
    public R<com.douplus.douplus.domain.DouplusTaskVO> getById(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        com.douplus.douplus.domain.DouplusTask task = taskService.getById(id);
        if (task == null || !task.getUserId().equals(userId)) {
            return R.fail("任务不存在");
        }
        return R.ok(com.douplus.douplus.domain.DouplusTaskVO.fromEntity(task));
    }

    /**
     * 取消投放任务
     */
    @PostMapping("/{id}/cancel")
    public R<Void> cancelTask(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        taskService.cancelTask(userId, id);
        return R.ok(null, "任务已取消");
    }

    /**
     * 删除投放任务（仅可删除失败状态的任务）
     */
    @DeleteMapping("/{id}")
    public R<Void> deleteTask(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        com.douplus.douplus.domain.DouplusTask task = taskService.getById(id);
        if (task == null || !task.getUserId().equals(userId)) {
            throw new BusinessException("任务不存在");
        }
        if (!"FAIL".equals(task.getStatus())) {
            throw new BusinessException("只能删除失败状态的任务");
        }
        taskService.removeById(id);
        log.info("用户{}删除了失败任务: {}", userId, id);
        return R.ok(null, "任务已删除");
    }

    /**
     * 同步DOU+历史订单（异步）
     */
    @PostMapping("/sync/{accountId}")
    public R<Map<String, Object>> syncOrders(@PathVariable Long accountId) {
        Long userId = SecurityUtils.getCurrentUserId();
        
        // 检查是否正在同步
        Map<String, Object> currentStatus = syncStatusMap.get(userId);
        if (currentStatus != null && "syncing".equals(currentStatus.get("status"))) {
            return R.ok(currentStatus, "正在同步中，请稍候...");
        }
        
        // 初始化同步状态
        Map<String, Object> status = new ConcurrentHashMap<>();
        status.put("status", "syncing");
        status.put("count", 0);
        status.put("message", "同步开始...");
        syncStatusMap.put(userId, status);
        
        // 异步执行同步
        syncExecutor.submit(() -> {
            try {
                int count = taskService.syncDouplusOrders(userId, accountId);
                status.put("status", "completed");
                status.put("count", count);
                status.put("message", "同步完成，共同步" + count + "个订单");
                log.info("用户{}同步完成，共{}条订单", userId, count);
            } catch (Exception e) {
                status.put("status", "error");
                status.put("message", "同步失败: " + e.getMessage());
                log.error("用户{}同步失败", userId, e);
            }
        });
        
        return R.ok(status, "同步已开始，请稍候查看结果");
    }
    
    /**
     * 查询同步状态
     */
    @GetMapping("/sync-status")
    public R<Map<String, Object>> getSyncStatus() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> status = syncStatusMap.get(userId);
        if (status == null) {
            status = Map.of("status", "idle", "count", 0, "message", "无同步任务");
        }
        return R.ok(status);
    }

    /**
     * 同步所有账号的DOU+历史订单（异步）
     */
    @PostMapping("/sync-all")
    public R<Map<String, Object>> syncAllOrders() {
        Long userId = SecurityUtils.getCurrentUserId();
        
        // 检查是否正在同步
        Map<String, Object> currentStatus = syncStatusMap.get(userId);
        if (currentStatus != null && "syncing".equals(currentStatus.get("status"))) {
            return R.ok(currentStatus, "正在同步中，请稍候...");
        }
        
        // 初始化同步状态
        Map<String, Object> status = new ConcurrentHashMap<>();
        status.put("status", "syncing");
        status.put("count", 0);
        status.put("message", "同步开始...");
        syncStatusMap.put(userId, status);
        
        var accounts = accountService.listByUserId(userId);
        
        // 异步执行同步
        syncExecutor.submit(() -> {
            int totalCount = 0;
            int totalUpdated = 0;
            for (var account : accounts) {
                try {
                    status.put("message", "正在同步账号: " + account.getNickname());
                    int count = taskService.syncDouplusOrders(userId, account.getId());
                    totalCount += count;
                    status.put("count", totalCount);
                } catch (Exception e) {
                    log.warn("同步账号{}的订单失败: {}", account.getNickname(), e.getMessage());
                }
            }
            status.put("status", "completed");
            if (totalCount > 0) {
                status.put("message", "同步完成，新增" + totalCount + "个订单");
            } else {
                status.put("message", "同步完成，无新订单（已有订单数据已更新）");
            }
            log.info("用户{}同步所有账号完成，新增{}条订单", userId, totalCount);
        });
        
        return R.ok(status, "同步已开始，请稍候查看结果");
    }
}