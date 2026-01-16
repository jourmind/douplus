package com.douplus.comment.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.douplus.comment.domain.KeywordBlacklist;
import org.apache.ibatis.annotations.Mapper;

/**
 * 敏感词/黑名单Mapper
 */
@Mapper
public interface KeywordBlacklistMapper extends BaseMapper<KeywordBlacklist> {
}
