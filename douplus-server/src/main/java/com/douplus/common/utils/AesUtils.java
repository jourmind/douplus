package com.douplus.common.utils;

import cn.hutool.crypto.symmetric.AES;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/**
 * AES加密工具类 - 用于加密敏感信息（如Token）
 */
public class AesUtils {
    
    private static final Logger log = LoggerFactory.getLogger(AesUtils.class);
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
     * 解密 - 自动识别AES加密或Base64编码
     * 兼容PHP OAuth回调保存的Base64编码token
     */
    public static String decrypt(String encryptedContent) {
        if (encryptedContent == null || encryptedContent.isEmpty()) {
            return encryptedContent;
        }
        
        // 首先尝试AES解密
        try {
            String decrypted = aes.decryptStr(encryptedContent);
            // AES解密成功后检查是否是有效的token格式
            if (decrypted != null && !decrypted.isEmpty() && isPrintableString(decrypted)) {
                return decrypted;
            }
        } catch (Exception e) {
            // AES解密失败，尝试Base64解码
            log.debug("AES解密失败，尝试Base64解码: {}", e.getMessage());
        }
        
        // 尝试Base64解码（PHP OAuth回调保存的格式）
        try {
            byte[] decoded = Base64.getDecoder().decode(encryptedContent);
            String result = new String(decoded, StandardCharsets.UTF_8);
            if (isPrintableString(result)) {
                log.debug("使用Base64解码成功");
                return result;
            }
        } catch (Exception e) {
            log.debug("Base64解码失败: {}", e.getMessage());
        }
        
        // 都失败了，返回原始内容（可能已经是明文）
        log.warn("解密失败，返回原始内容");
        return encryptedContent;
    }
    
    /**
     * 检查字符串是否是可打印字符（用于验证解密结果）
     */
    private static boolean isPrintableString(String str) {
        if (str == null || str.isEmpty()) {
            return false;
        }
        for (char c : str.toCharArray()) {
            if (c < 32 || c > 126) {
                // 允许一些常见的扩展ASCII字符
                if (c != '\n' && c != '\r' && c != '\t') {
                    return false;
                }
            }
        }
        return true;
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
