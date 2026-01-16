package com.douplus.auth.controller;

import com.douplus.auth.domain.*;
import com.douplus.auth.security.JwtUtils;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.auth.service.SysUserService;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.common.result.ResultCode;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 认证控制器
 */
@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final SysUserService userService;
    private final JwtUtils jwtUtils;

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public R<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        // 查询用户
        SysUser user = userService.getByUsername(request.getUsername());
        if (user == null) {
            throw new BusinessException(ResultCode.LOGIN_FAILED);
        }

        // 验证状态
        if (user.getStatus() != 1) {
            throw new BusinessException(ResultCode.ACCOUNT_DISABLED);
        }

        // 验证密码
        if (!userService.validatePassword(request.getPassword(), user.getPassword())) {
            throw new BusinessException(ResultCode.LOGIN_FAILED);
        }

        // 生成Token
        String token = jwtUtils.generateToken(user.getId(), user.getUsername());

        // 更新登录信息
        userService.updateLoginInfo(user.getId(), SecurityUtils.getRequestIp());

        // 构建响应
        LoginResponse response = LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .expiresIn(jwtUtils.getExpirationSeconds())
                .user(UserVO.fromEntity(user))
                .build();

        log.info("用户登录成功: {}", user.getUsername());
        return R.ok(response, "登录成功");
    }

    /**
     * 获取当前用户信息
     */
    @GetMapping("/info")
    public R<UserVO> getUserInfo() {
        Long userId = SecurityUtils.getCurrentUserId();
        if (userId == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED);
        }
        SysUser user = userService.getById(userId);
        return R.ok(UserVO.fromEntity(user));
    }

    /**
     * 修改密码
     */
    @PostMapping("/password")
    public R<Void> changePassword(@RequestBody ChangePasswordRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.changePassword(userId, request.getOldPassword(), request.getNewPassword());
        return R.ok(null, "密码修改成功");
    }

    /**
     * 设置投放密码
     */
    @PostMapping("/invest-password")
    public R<Void> setInvestPassword(@RequestBody SetInvestPasswordRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.setInvestPassword(userId, request.getInvestPassword());
        return R.ok(null, "投放密码设置成功");
    }

    /**
     * 验证投放密码
     */
    @PostMapping("/verify-invest-password")
    public R<Boolean> verifyInvestPassword(@RequestBody VerifyInvestPasswordRequest request) {
        Long userId = SecurityUtils.getCurrentUserId();
        boolean valid = userService.validateInvestPassword(userId, request.getInvestPassword());
        if (!valid) {
            throw new BusinessException(ResultCode.INVEST_PASSWORD_ERROR);
        }
        return R.ok(true);
    }

    /**
     * 退出登录
     */
    @PostMapping("/logout")
    public R<Void> logout() {
        // JWT无状态，客户端清除Token即可
        return R.ok(null, "退出成功");
    }
}
