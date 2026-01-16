package com.douplus.auth.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.douplus.auth.domain.SysUser;
import com.douplus.auth.mapper.SysUserMapper;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.ResultCode;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 系统用户Service
 */
@Service
@RequiredArgsConstructor
public class SysUserService extends ServiceImpl<SysUserMapper, SysUser> {

    private final PasswordEncoder passwordEncoder;

    /**
     * 根据用户名查询用户
     */
    public SysUser getByUsername(String username) {
        return getOne(new LambdaQueryWrapper<SysUser>()
                .eq(SysUser::getUsername, username)
                .eq(SysUser::getDeleted, 0));
    }

    /**
     * 创建用户
     */
    public SysUser createUser(String username, String password, String nickname) {
        // 检查用户名是否已存在
        if (getByUsername(username) != null) {
            throw new BusinessException("用户名已存在");
        }

        SysUser user = new SysUser();
        user.setUsername(username);
        user.setPassword(passwordEncoder.encode(password));
        user.setNickname(nickname != null ? nickname : username);
        user.setStatus(1);
        save(user);
        return user;
    }

    /**
     * 验证密码
     */
    public boolean validatePassword(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }

    /**
     * 修改密码
     */
    public void changePassword(Long userId, String oldPassword, String newPassword) {
        SysUser user = getById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        if (!validatePassword(oldPassword, user.getPassword())) {
            throw new BusinessException(ResultCode.PASSWORD_ERROR);
        }
        user.setPassword(passwordEncoder.encode(newPassword));
        updateById(user);
    }

    /**
     * 设置/修改投放密码
     */
    public void setInvestPassword(Long userId, String investPassword) {
        SysUser user = getById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        user.setInvestPassword(passwordEncoder.encode(investPassword));
        updateById(user);
    }

    /**
     * 验证投放密码
     */
    public boolean validateInvestPassword(Long userId, String investPassword) {
        SysUser user = getById(userId);
        if (user == null || user.getInvestPassword() == null) {
            return false;
        }
        return passwordEncoder.matches(investPassword, user.getInvestPassword());
    }

    /**
     * 更新最后登录信息
     */
    public void updateLoginInfo(Long userId, String ip) {
        baseMapper.updateLoginInfo(userId, LocalDateTime.now(), ip);
    }
}
