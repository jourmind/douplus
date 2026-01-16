package com.douplus.auth.domain;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 登录请求DTO
 */
@Data
public class LoginRequest {

    @NotBlank(message = "用户名不能为空")
    private String username;

    @NotBlank(message = "密码不能为空")
    private String password;

    /**
     * 验证码（预留）
     */
    private String captcha;

    /**
     * 验证码ID（预留）
     */
    private String captchaId;
}
