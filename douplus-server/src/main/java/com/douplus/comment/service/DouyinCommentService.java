package com.douplus.comment.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.comment.domain.DouyinComment;
import com.douplus.comment.domain.KeywordBlacklist;
import com.douplus.comment.mapper.DouyinCommentMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 评论Service
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DouyinCommentService extends ServiceImpl<DouyinCommentMapper, DouyinComment> {

    private final KeywordBlacklistService blacklistService;

    /**
     * 分页查询评论
     */
    public Page<DouyinComment> pageComments(Long userId, Long accountId, String itemId, 
                                            Integer status, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<DouyinComment> wrapper = new LambdaQueryWrapper<DouyinComment>()
                .eq(DouyinComment::getDeleted, 0)
                .orderByDesc(DouyinComment::getCommentTime);
        
        if (accountId != null) {
            wrapper.eq(DouyinComment::getAccountId, accountId);
        }
        if (itemId != null && !itemId.isEmpty()) {
            wrapper.eq(DouyinComment::getItemId, itemId);
        }
        if (status != null) {
            wrapper.eq(DouyinComment::getStatus, status);
        }
        
        return page(new Page<>(pageNum, pageSize), wrapper);
    }

    /**
     * 查询负面评论
     */
    public Page<DouyinComment> pageNegativeComments(Long accountId, Integer pageNum, Integer pageSize) {
        return page(new Page<>(pageNum, pageSize),
                new LambdaQueryWrapper<DouyinComment>()
                        .eq(DouyinComment::getAccountId, accountId)
                        .eq(DouyinComment::getIsNegative, 1)
                        .eq(DouyinComment::getStatus, DouyinComment.STATUS_NORMAL)
                        .eq(DouyinComment::getDeleted, 0)
                        .orderByDesc(DouyinComment::getCommentTime));
    }

    /**
     * 检查评论是否命中敏感词
     */
    public String checkKeyword(Long userId, String content) {
        if (content == null || content.isEmpty()) {
            return null;
        }
        List<KeywordBlacklist> keywords = blacklistService.listByUserId(userId, KeywordBlacklist.TYPE_KEYWORD);
        for (KeywordBlacklist kw : keywords) {
            if (content.contains(kw.getKeyword())) {
                return kw.getKeyword();
            }
        }
        return null;
    }

    /**
     * 标记为负面评论
     */
    public void markNegative(Long commentId, String keyword) {
        DouyinComment comment = getById(commentId);
        if (comment != null) {
            comment.setIsNegative(1);
            comment.setKeywordHit(keyword);
            updateById(comment);
        }
    }

    /**
     * 标记待删除
     */
    public void markPendingDelete(Long commentId) {
        DouyinComment comment = getById(commentId);
        if (comment != null) {
            comment.setStatus(DouyinComment.STATUS_PENDING_DELETE);
            updateById(comment);
        }
    }

    /**
     * 标记已删除
     */
    public void markDeleted(Long commentId) {
        DouyinComment comment = getById(commentId);
        if (comment != null) {
            comment.setStatus(DouyinComment.STATUS_DELETED);
            updateById(comment);
        }
    }

    /**
     * 查询待删除的评论
     */
    public List<DouyinComment> listPendingDeleteComments() {
        return list(new LambdaQueryWrapper<DouyinComment>()
                .eq(DouyinComment::getStatus, DouyinComment.STATUS_PENDING_DELETE)
                .eq(DouyinComment::getDeleted, 0)
                .last("LIMIT 20"));
    }

    /**
     * 批量保存评论（同步时使用）
     */
    public void batchSaveComments(List<DouyinComment> comments, Long userId) {
        // 获取敏感词列表
        List<String> keywords = blacklistService.listByUserId(userId, KeywordBlacklist.TYPE_KEYWORD)
                .stream()
                .map(KeywordBlacklist::getKeyword)
                .collect(Collectors.toList());
        
        for (DouyinComment comment : comments) {
            // 检查是否已存在
            DouyinComment existing = getOne(new LambdaQueryWrapper<DouyinComment>()
                    .eq(DouyinComment::getCommentId, comment.getCommentId())
                    .eq(DouyinComment::getDeleted, 0));
            
            if (existing == null) {
                // 检查敏感词
                for (String kw : keywords) {
                    if (comment.getContent() != null && comment.getContent().contains(kw)) {
                        comment.setIsNegative(1);
                        comment.setKeywordHit(kw);
                        break;
                    }
                }
                save(comment);
            }
        }
    }
}
