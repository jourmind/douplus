package com.douplus.auth.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.douplus.auth.domain.SysUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;

/**
 * 系统用户Mapper
 */
@Mapper
public interface SysUserMapper extends BaseMapper<SysUser> {

    /**
     * 更新最后登录信息
     */
    @Update("UPDATE sys_user SET last_login_time = #{loginTime}, last_login_ip = #{ip} WHERE id = #{userId}")
    void updateLoginInfo(@Param("userId") Long userId, @Param("loginTime") LocalDateTime loginTime, @Param("ip") String ip);
}
