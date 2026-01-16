package com.douplus.douplus.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.result.R;
import com.douplus.douplus.domain.CreateTaskRequest;
import com.douplus.douplus.domain.DouplusTask;
import com.douplus.douplus.domain.DouplusTaskVO;
import com.douplus.douplus.service.DouplusTaskService;
import jakarta.validation.Valid;
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
     * 创建投放任务
     */
    @PostMapping("/create")
    public R<List<DouplusTask>> createTask(@Valid @RequestBody CreateTaskRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        List<DouplusTask> tasks = taskService.createTasks(userId, request);
        return R.ok(tasks, "投放任务创建成功，共" + tasks.size() + "个任务");
    }

    /**
     * 分页查询投放记录
     */
    @GetMapping("/page")
    public R<Page<DouplusTaskVO>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String status) {
        Long userId = SecurityUtils.getCurrentUserId();
        Page<DouplusTaskVO> page = taskService.pageByUserId(userId, pageNum, pageSize, status);
        return R.ok(page);
    }

    /**
     * 获取任务详情
     */
    @GetMapping("/{id}")
    public R<DouplusTaskVO> getById(@PathVariable Long id) {
        DouplusTask task = taskService.getById(id);
        if (task == null || !task.getUserId().equals(SecurityUtils.getCurrentUserId())) {
            return R.fail("任务不存在");
        }
        return R.ok(DouplusTaskVO.fromEntity(task));
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
     * 统计投放数据
     */
    @GetMapping("/stats")
    public R<TaskStats> getStats() {
        Long userId = SecurityUtils.getCurrentUserId();
        // TODO: 实现统计逻辑
        TaskStats stats = new TaskStats();
        return R.ok(stats);
    }

    @lombok.Data
    static class TaskStats {
        private Integer totalTasks = 0;
        private Integer successTasks = 0;
        private Integer failTasks = 0;
        private Integer runningTasks = 0;
        private java.math.BigDecimal totalBudget = java.math.BigDecimal.ZERO;
        private java.math.BigDecimal totalCost = java.math.BigDecimal.ZERO;
    }
}
