package com.douplus.comment.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.comment.domain.KeywordBlacklist;
import com.douplus.comment.mapper.KeywordBlacklistMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 敏感词/黑名单Service
 */
@Slf4j
@Service
public class KeywordBlacklistService extends ServiceImpl<KeywordBlacklistMapper, KeywordBlacklist> {

    /**
     * 根据用户ID和类型获取列表
     */
    public List<KeywordBlacklist> listByUserId(Long userId, Integer type) {
        LambdaQueryWrapper<KeywordBlacklist> wrapper = new LambdaQueryWrapper<KeywordBlacklist>()
                .eq(KeywordBlacklist::getUserId, userId)
                .eq(KeywordBlacklist::getDeleted, 0);
        if (type != null) {
            wrapper.eq(KeywordBlacklist::getType, type);
        }
        return list(wrapper);
    }

    /**
     * 添加敏感词
     */
    public void addKeyword(Long userId, String keyword, Integer type, boolean autoDelete) {
        // 检查是否已存在
        KeywordBlacklist existing = getOne(new LambdaQueryWrapper<KeywordBlacklist>()
                .eq(KeywordBlacklist::getUserId, userId)
                .eq(KeywordBlacklist::getKeyword, keyword)
                .eq(KeywordBlacklist::getType, type)
                .eq(KeywordBlacklist::getDeleted, 0));
        
        if (existing != null) {
            return; // 已存在，不重复添加
        }
        
        KeywordBlacklist blacklist = new KeywordBlacklist();
        blacklist.setUserId(userId);
        blacklist.setKeyword(keyword);
        blacklist.setType(type);
        blacklist.setAutoDelete(autoDelete ? 1 : 0);
        save(blacklist);
    }

    /**
     * 删除敏感词
     */
    public void deleteKeyword(Long userId, Long id) {
        KeywordBlacklist kw = getById(id);
        if (kw != null && kw.getUserId().equals(userId)) {
            removeById(id);
        }
    }

    /**
     * 批量添加敏感词
     */
    public void batchAddKeywords(Long userId, List<String> keywords, Integer type, boolean autoDelete) {
        for (String keyword : keywords) {
            addKeyword(userId, keyword.trim(), type, autoDelete);
        }
    }
}
