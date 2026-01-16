package com.douplus.auth.domain;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 设置投放密码请求
 */
@Data
public class SetInvestPasswordRequest {

    @NotBlank(message = "投放密码不能为空")
    private String investPassword;
}
