package com.douplus.comment.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.comment.domain.DouyinComment;
import com.douplus.comment.domain.KeywordBlacklist;
import com.douplus.comment.service.DouyinCommentService;
import com.douplus.comment.service.KeywordBlacklistService;
import com.douplus.common.result.R;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 评论管理Controller
 */
@Slf4j
@RestController
@RequestMapping("/comment")
@RequiredArgsConstructor
public class CommentController {

    private final DouyinCommentService commentService;
    private final KeywordBlacklistService blacklistService;

    /**
     * 分页查询评论
     */
    @GetMapping("/page")
    public R<Page<DouyinComment>> pageComments(
            @RequestParam(required = false) Long accountId,
            @RequestParam(required = false) String itemId,
            @RequestParam(required = false) Integer status,
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "20") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        Page<DouyinComment> page = commentService.pageComments(userId, accountId, itemId, status, pageNum, pageSize);
        return R.ok(page);
    }

    /**
     * 查询负面评论
     */
    @GetMapping("/negative")
    public R<Page<DouyinComment>> pageNegativeComments(
            @RequestParam Long accountId,
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "20") Integer pageSize) {
        Page<DouyinComment> page = commentService.pageNegativeComments(accountId, pageNum, pageSize);
        return R.ok(page);
    }

    /**
     * 标记评论为待删除
     */
    @PostMapping("/{id}/delete")
    public R<Void> markDelete(@PathVariable Long id) {
        commentService.markPendingDelete(id);
        return R.ok(null, "已标记删除");
    }

    /**
     * 批量标记删除
     */
    @PostMapping("/batch-delete")
    public R<Void> batchMarkDelete(@RequestBody BatchDeleteRequest request) {
        for (Long id : request.getIds()) {
            commentService.markPendingDelete(id);
        }
        return R.ok(null, "已标记删除" + request.getIds().size() + "条评论");
    }

    // ============ 敏感词管理 ============

    /**
     * 获取敏感词列表
     */
    @GetMapping("/keyword/list")
    public R<List<KeywordBlacklist>> listKeywords(@RequestParam(required = false) Integer type) {
        Long userId = SecurityUtils.getCurrentUserId();
        List<KeywordBlacklist> list = blacklistService.listByUserId(userId, type);
        return R.ok(list);
    }

    /**
     * 添加敏感词
     */
    @PostMapping("/keyword/add")
    public R<Void> addKeyword(@RequestBody AddKeywordRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        int type = request.getType() != null ? request.getType() : KeywordBlacklist.TYPE_KEYWORD;
        boolean autoDelete = request.getAutoDelete() != null ? request.getAutoDelete() : true;
        blacklistService.addKeyword(userId, request.getKeyword(), type, autoDelete);
        return R.ok(null, "添加成功");
    }

    /**
     * 批量添加敏感词
     */
    @PostMapping("/keyword/batch-add")
    public R<Void> batchAddKeywords(@RequestBody BatchAddKeywordRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        int type = request.getType() != null ? request.getType() : KeywordBlacklist.TYPE_KEYWORD;
        boolean autoDelete = request.getAutoDelete() != null ? request.getAutoDelete() : true;
        blacklistService.batchAddKeywords(userId, request.getKeywords(), type, autoDelete);
        return R.ok(null, "添加成功");
    }

    /**
     * 删除敏感词
     */
    @DeleteMapping("/keyword/{id}")
    public R<Void> deleteKeyword(@PathVariable Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        blacklistService.deleteKeyword(userId, id);
        return R.ok(null, "删除成功");
    }

    // ======== 请求类 ========

    @Data
    static class BatchDeleteRequest {
        private List<Long> ids;
    }

    @Data
    static class AddKeywordRequest {
        private String keyword;
        private Integer type;
        private Boolean autoDelete;
    }

    @Data
    static class BatchAddKeywordRequest {
        private List<String> keywords;
        private Integer type;
        private Boolean autoDelete;
    }
}
