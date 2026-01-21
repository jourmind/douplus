package com.douplus.account.controller;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONArray;
import com.alibaba.fastjson2.JSONObject;
import com.douplus.account.domain.DouyinAccount;
import com.douplus.account.service.DouyinAccountService;
import com.douplus.auth.security.SecurityUtils;
import com.douplus.common.exception.BusinessException;
import com.douplus.common.result.R;
import com.douplus.common.result.ResultCode;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 抖音视频管理Controller
 */
@Slf4j
@RestController
@RequestMapping("/video")
@RequiredArgsConstructor
public class DouyinVideoController {

    private final DouyinAccountService accountService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${douyin.api.base-url:https://open.douyin.com}")
    private String apiBaseUrl;

    /**
     * 获取账号的视频列表
     */
    @GetMapping("/list/{accountId}")
    public R<List<VideoInfo>> getVideoList(
            @PathVariable Long accountId,
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "20") Integer pageSize) {
        
        Long userId = SecurityUtils.getCurrentUserId();
        DouyinAccount account = accountService.getByIdAndUserId(accountId, userId);
        if (account == null) {
            throw new BusinessException(ResultCode.ACCOUNT_NOT_FOUND);
        }
        
        try {
            // 解密access_token
            String accessToken = decryptToken(account.getAccessToken());
            String openId = account.getOpenId();
            
            // 调用抖音API获取视频列表
            List<VideoInfo> videos = fetchVideosFromApi(accessToken, openId, page, pageSize);
            
            return R.ok(videos);
        } catch (Exception e) {
            log.error("获取视频列表失败", e);
            return R.ok(new ArrayList<>());
        }
    }

    /**
     * 从抖音开放平台API获取视频列表
     */
    private List<VideoInfo> fetchVideosFromApi(String accessToken, String openId, int page, int pageSize) {
        // 抖音开放平台视频列表API
        String url = apiBaseUrl + "/api/douyin/v1/video/video_list/";
        
        // 构建URL参数 - cursor用于分页，第一页传空
        long cursor = (page - 1) * pageSize;
        String fullUrl = url + "?open_id=" + openId + "&cursor=" + cursor + "&count=" + pageSize;
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("access-token", accessToken);
        
        HttpEntity<String> entity = new HttpEntity<>(headers);
        
        try {
            log.info("调用抖音视频列表API: {}, open_id: {}", fullUrl, openId);
            
            ResponseEntity<String> response = restTemplate.exchange(
                fullUrl,
                HttpMethod.GET,
                entity,
                String.class
            );
            
            log.info("抖音视频列表API响应: {}", response.getBody());
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JSONObject result = JSON.parseObject(response.getBody());
                JSONObject data = result.getJSONObject("data");
                
                if (data != null) {
                    int errCode = data.getIntValue("error_code");
                    if (errCode == 0) {
                        JSONArray list = data.getJSONArray("list");
                        List<VideoInfo> videos = new ArrayList<>();
                        
                        if (list != null && !list.isEmpty()) {
                            for (int i = 0; i < list.size(); i++) {
                                JSONObject item = list.getJSONObject(i);
                                VideoInfo video = new VideoInfo();
                                video.setId(item.getString("item_id"));
                                video.setTitle(item.getString("title"));
                                video.setCoverUrl(item.getString("cover"));
                                // 时长单位是毫秒，转换为秒
                                Long videoDuration = item.getLong("video_duration");
                                if (videoDuration != null) {
                                    video.setDuration((int)(videoDuration / 1000));
                                }
                                video.setCreateTime(item.getString("create_time"));
                                
                                // 统计数据
                                JSONObject statistics = item.getJSONObject("statistics");
                                if (statistics != null) {
                                    video.setPlayCount(statistics.getLong("play_count"));
                                    video.setLikeCount(statistics.getLong("digg_count"));
                                    video.setCommentCount(statistics.getLong("comment_count"));
                                    video.setShareCount(statistics.getLong("share_count"));
                                }
                                videos.add(video);
                            }
                            return videos;
                        }
                    } else {
                        log.warn("抖音API返回错误: error_code={}, description={}", 
                            errCode, data.getString("description"));
                    }
                }
            }
        } catch (Exception e) {
            log.error("调用抖音视频列表API失败: {}", e.getMessage(), e);
        }
        
        // API调用失败时返回空列表
        return new ArrayList<>();
    }

    /**
     * 模拟视频数据（用于测试）
     */
    private List<VideoInfo> getMockVideos() {
        List<VideoInfo> videos = new ArrayList<>();
        
        VideoInfo v1 = new VideoInfo();
        v1.setId("7123456789012345678");
        v1.setTitle("李子柒美食篇：传统手工月饼制作");
        v1.setCoverUrl("https://p3-pc.douyinpic.com/img/sample1.jpg");
        v1.setDuration(185);
        v1.setCreateTime("2026-01-15 14:30:00");
        v1.setPlayCount(125000L);
        v1.setLikeCount(8500L);
        v1.setCommentCount(320L);
        videos.add(v1);
        
        VideoInfo v2 = new VideoInfo();
        v2.setId("7123456789012345679");
        v2.setTitle("你知道我这三年怎么过的吗 #李子柒回归");
        v2.setCoverUrl("https://p3-pc.douyinpic.com/img/sample2.jpg");
        v2.setDuration(62);
        v2.setCreateTime("2026-01-14 10:15:00");
        v2.setPlayCount(2500000L);
        v2.setLikeCount(185000L);
        v2.setCommentCount(12500L);
        videos.add(v2);
        
        VideoInfo v3 = new VideoInfo();
        v3.setId("7123456789012345680");
        v3.setTitle("春节特辑：传统年货制作合集");
        v3.setCoverUrl("https://p3-pc.douyinpic.com/img/sample3.jpg");
        v3.setDuration(320);
        v3.setCreateTime("2026-01-10 09:00:00");
        v3.setPlayCount(85000L);
        v3.setLikeCount(6200L);
        v3.setCommentCount(180L);
        videos.add(v3);
        
        return videos;
    }

    /**
     * 解密Token
     */
    private String decryptToken(String encryptedToken) {
        if (encryptedToken == null || encryptedToken.isEmpty()) {
            return "";
        }
        try {
            // 尝试Base64解码
            return new String(Base64.getDecoder().decode(encryptedToken));
        } catch (Exception e) {
            // 如果不是Base64，返回原值
            return encryptedToken;
        }
    }

    /**
     * 视频信息VO
     */
    @Data
    public static class VideoInfo {
        private String id;
        private String title;
        private String coverUrl;
        private Integer duration;
        private String createTime;
        private Long playCount;
        private Long likeCount;
        private Long commentCount;
        private Long shareCount;
    }
}
