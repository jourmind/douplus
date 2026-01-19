package com.douplus.douplus.controller;

import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.douplus.domain.CreateTaskRequest;
import com.douplus.douplus.service.DouplusTaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * DOU+投放任务Controller
 */
@Slf4j
@RestController
@RequestMapping("/douplus/task")
@RequiredArgsConstructor
public class DouplusTaskController {

    private final DouplusTaskService taskService;

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
            @RequestParam(required = false) String status) {
        Long userId = SecurityUtils.getCurrentUserId();
        var result = taskService.pageByUserId(userId, pageNum, pageSize, status);
        return R.ok(result);
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
}