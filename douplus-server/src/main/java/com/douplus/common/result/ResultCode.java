package com.douplus.common.result;

import lombok.Getter;

/**
 * 错误码枚举
 */
@Getter
public enum ResultCode {
    // 通用
    SUCCESS(200, "操作成功"),
    ERROR(500, "操作失败"),
    PARAM_ERROR(400, "参数错误"),
    NOT_FOUND(404, "资源不存在"),

    // 认证相关 1xxx
    UNAUTHORIZED(1001, "未登录或token已过期"),
    TOKEN_INVALID(1002, "token无效"),
    TOKEN_EXPIRED(1003, "token已过期"),
    ACCESS_DENIED(1004, "无权限访问"),
    LOGIN_FAILED(1005, "用户名或密码错误"),
    ACCOUNT_DISABLED(1006, "账号已禁用"),
    PASSWORD_ERROR(1007, "密码错误"),

    // 账号相关 2xxx
    ACCOUNT_NOT_FOUND(2001, "抖音账号不存在"),
    ACCOUNT_TOKEN_EXPIRED(2002, "抖音授权已过期，请重新授权"),
    ACCOUNT_BINDIED(2003, "该抖音账号已绑定"),

    // 投放相关 3xxx
    TASK_NOT_FOUND(3001, "投放任务不存在"),
    TASK_STATUS_ERROR(3002, "任务状态错误"),
    BUDGET_EXCEED_LIMIT(3003, "投放金额超出限额"),
    DAILY_LIMIT_EXCEED(3004, "已达到当日投放限额"),
    VIDEO_NOT_FOUND(3005, "视频不存在"),
    DOUPLUS_API_ERROR(3006, "抖音API调用失败"),
    INSUFFICIENT_BALANCE(3007, "账户余额不足"),
    INVEST_PASSWORD_ERROR(3008, "投放密码错误"),

    // 评论相关 4xxx
    COMMENT_NOT_FOUND(4001, "评论不存在"),
    COMMENT_DELETE_FAILED(4002, "评论删除失败"),

    // 系统相关 9xxx
    SYSTEM_ERROR(9001, "系统异常"),
    RATE_LIMIT(9002, "请求过于频繁，请稍后再试"),
    SERVICE_UNAVAILABLE(9003, "服务暂不可用");

    private final Integer code;
    private final String message;

    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
