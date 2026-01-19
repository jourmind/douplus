package com.douplus.account.task;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.common.utils.AesUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Token刷新定时任务
 * 自动刷新即将过期的抖音账号Token
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TokenRefreshTask {

    private final DouyinAccountService accountService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${douyin.api.app-id:}")
    private String appId;

    @Value("${douyin.api.app-secret:}")
    private String appSecret;

    /**
     * 每6小时执行一次Token刷新检查
     */
    @Scheduled(fixedRate = 6 * 60 * 60 * 1000, initialDelay = 60000)
    public void refreshExpiringTokens() {
        log.info("=== 开始检查即将过期的Token ===");
        
        try {
            // 查询7天内即将过期的账号
            List<DouyinAccount> expiringAccounts = accountService.listExpiringAccounts();
            
            if (expiringAccounts.isEmpty()) {
                log.info("没有即将过期的Token需要刷新");
                return;
            }
            
            log.info("发现{}个即将过期的账号，开始刷新", expiringAccounts.size());
            
            int successCount = 0;
            int failCount = 0;
            
            for (DouyinAccount account : expiringAccounts) {
                try {
                    boolean success = refreshAccountToken(account);
                    if (success) {
                        successCount++;
                        log.info("账号[{}]Token刷新成功", account.getNickname());
                    } else {
                        failCount++;
                        log.warn("账号[{}]Token刷新失败", account.getNickname());
                    }
                } catch (Exception e) {
                    failCount++;
                    log.error("账号[{}]Token刷新异常: {}", account.getNickname(), e.getMessage());
                }
                
                // 避免请求过快
                Thread.sleep(1000);
            }
            
            log.info("=== Token刷新完成: 成功{}个, 失败{}个 ===", successCount, failCount);
            
        } catch (Exception e) {
            log.error("Token刷新任务执行异常", e);
        }
    }

    /**
     * 刷新单个账号的Token
     */
    private boolean refreshAccountToken(DouyinAccount account) {
        try {
            // 解密refresh_token
            String refreshToken = account.getRefreshToken();
            if (refreshToken == null || refreshToken.isEmpty()) {
                log.warn("账号[{}]没有refresh_token，无法刷新", account.getNickname());
                return false;
            }
            
            // 尝试解密（如果是加密的）
            try {
                refreshToken = AesUtils.decrypt(refreshToken);
            } catch (Exception e) {
                // 可能是Base64编码的，尝试解码
                try {
                    refreshToken = new String(java.util.Base64.getDecoder().decode(refreshToken));
                } catch (Exception e2) {
                    // 使用原始值
                }
            }
            
            // 调用刷新Token API
            String url = "https://ad.oceanengine.com/open_api/oauth2/refresh_token/";
            
            Map<String, Object> params = new HashMap<>();
            params.put("app_id", appId);
            params.put("secret", appSecret);
            params.put("grant_type", "refresh_token");
            params.put("refresh_token", refreshToken);
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> entity = new HttpEntity<>(JSON.toJSONString(params), headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                url, 
                HttpMethod.POST, 
                entity, 
                String.class
            );
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JSONObject result = JSON.parseObject(response.getBody());
                JSONObject data = result.getJSONObject("data");
                
                if (data != null && data.getString("access_token") != null) {
                    String newAccessToken = data.getString("access_token");
                    String newRefreshToken = data.getString("refresh_token");
                    Integer expiresIn = data.getInteger("expires_in");
                    
                    if (expiresIn == null) {
                        expiresIn = 86400; // 默认24小时
                    }
                    
                    LocalDateTime newExpiresAt = LocalDateTime.now().plusSeconds(expiresIn);
                    
                    // 更新数据库
                    accountService.refreshToken(
                        account.getId(),
                        newAccessToken,
                        newRefreshToken != null ? newRefreshToken : refreshToken,
                        newExpiresAt
                    );
                    
                    return true;
                } else {
                    String errMsg = result.getString("message");
                    log.error("刷新Token失败: {}", errMsg);
                    
                    // 如果refresh_token也过期了，标记账号为失效
                    if (errMsg != null && errMsg.contains("expired")) {
                        accountService.setTokenExpired(account.getId());
                    }
                    return false;
                }
            }
            
            return false;
            
        } catch (Exception e) {
            log.error("刷新Token异常: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * 手动触发刷新指定账号的Token
     */
    public boolean manualRefresh(Long accountId) {
        DouyinAccount account = accountService.getById(accountId);
        if (account == null) {
            return false;
        }
        return refreshAccountToken(account);
    }
}
