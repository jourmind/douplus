package com.douplus.auth.domain;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 验证投放密码请求
 */
@Data
public class VerifyInvestPasswordRequest {

    @NotBlank(message = "投放密码不能为空")
    private String investPassword;
}
