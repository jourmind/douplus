package com.douplus.douplus.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.douplus.douplus.domain.DouplusTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * DOU+投放任务Mapper
 */
@Mapper
public interface DouplusTaskMapper extends BaseMapper<DouplusTask> {

    /**
     * 统计账号当日投放金额
     */
    @Select("SELECT COALESCE(SUM(budget), 0) FROM douplus_task " +
            "WHERE account_id = #{accountId} " +
            "AND status IN ('WAIT', 'RUNNING', 'SUCCESS') " +
            "AND DATE(create_time) = #{date} " +
            "AND deleted = 0")
    BigDecimal sumDailyBudget(@Param("accountId") Long accountId, @Param("date") LocalDate date);

    /**
     * 统计用户当日投放金额
     */
    @Select("SELECT COALESCE(SUM(budget), 0) FROM douplus_task " +
            "WHERE user_id = #{userId} " +
            "AND status IN ('WAIT', 'RUNNING', 'SUCCESS') " +
            "AND DATE(create_time) = #{date} " +
            "AND deleted = 0")
    BigDecimal sumUserDailyBudget(@Param("userId") Long userId, @Param("date") LocalDate date);
}
