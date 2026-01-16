package com.douplus.common.utils;

import cn.hutool.crypto.symmetric.AES;

import java.nio.charset.StandardCharsets;

/**
 * AES加密工具类 - 用于加密敏感信息（如Token）
 */
public class AesUtils {
    
    private static final String DEFAULT_KEY = "douplus-aes-key1"; // 16位密钥

    private static final AES aes = new AES(DEFAULT_KEY.getBytes(StandardCharsets.UTF_8));

    /**
     * 加密
     */
    public static String encrypt(String content) {
        if (content == null || content.isEmpty()) {
            return content;
        }
        return aes.encryptHex(content);
    }

    /**
     * 解密
     */
    public static String decrypt(String encryptedContent) {
        if (encryptedContent == null || encryptedContent.isEmpty()) {
            return encryptedContent;
        }
        return aes.decryptStr(encryptedContent);
    }

    /**
     * 使用自定义密钥加密
     */
    public static String encrypt(String content, String key) {
        if (content == null || content.isEmpty()) {
            return content;
        }
        AES customAes = new AES(padKey(key).getBytes(StandardCharsets.UTF_8));
        return customAes.encryptHex(content);
    }

    /**
     * 使用自定义密钥解密
     */
    public static String decrypt(String encryptedContent, String key) {
        if (encryptedContent == null || encryptedContent.isEmpty()) {
            return encryptedContent;
        }
        AES customAes = new AES(padKey(key).getBytes(StandardCharsets.UTF_8));
        return customAes.decryptStr(encryptedContent);
    }

    /**
     * 补齐密钥至16位
     */
    private static String padKey(String key) {
        if (key.length() >= 16) {
            return key.substring(0, 16);
        }
        StringBuilder sb = new StringBuilder(key);
        while (sb.length() < 16) {
            sb.append("0");
        }
        return sb.toString();
    }
}
