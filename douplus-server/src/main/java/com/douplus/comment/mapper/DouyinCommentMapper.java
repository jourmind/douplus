package com.douplus.comment.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.douplus.comment.domain.DouyinComment;
import org.apache.ibatis.annotations.Mapper;

/**
 * 评论Mapper
 */
@Mapper
public interface DouyinCommentMapper extends BaseMapper<DouyinComment> {
}
