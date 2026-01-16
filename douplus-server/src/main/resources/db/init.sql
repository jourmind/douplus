-- DOU+投放管理系统数据库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS douplus DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE douplus;

-- ========================================
-- 1. 系统用户表
-- ========================================
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码（加密）',
    nickname VARCHAR(50) COMMENT '昵称',
    avatar VARCHAR(255) COMMENT '头像URL',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    invest_password VARCHAR(255) COMMENT '投放密码（加密）',
    status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    last_login_time DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(50) COMMENT '最后登录IP',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_username (username),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 默认管理员账号（密码：admin123）
INSERT INTO sys_user (username, password, nickname, status) VALUES 
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iMGDXgnrbKjmIGvqbp/hM/FgFgGe', '管理员', 1);

-- ========================================
-- 2. 抖音账号表
-- ========================================
CREATE TABLE IF NOT EXISTS douyin_account (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '账号ID',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    open_id VARCHAR(100) NOT NULL COMMENT '抖音OpenID',
    union_id VARCHAR(100) COMMENT '抖音UnionID',
    nickname VARCHAR(100) COMMENT '抖音昵称',
    avatar VARCHAR(500) COMMENT '抖音头像',
    fans_count INT DEFAULT 0 COMMENT '粉丝数',
    following_count INT DEFAULT 0 COMMENT '关注数',
    total_favorited INT DEFAULT 0 COMMENT '获赞数',
    access_token TEXT COMMENT 'AccessToken（AES加密）',
    refresh_token TEXT COMMENT 'RefreshToken（AES加密）',
    token_expires_at DATETIME COMMENT 'Token过期时间',
    status TINYINT DEFAULT 1 COMMENT '状态：0-授权失效，1-正常',
    daily_limit DECIMAL(10,2) DEFAULT 10000.00 COMMENT '单日投放限额',
    balance DECIMAL(10,2) DEFAULT 0.00 COMMENT '账户余额',
    remark VARCHAR(500) COMMENT '备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_user_id (user_id),
    INDEX idx_open_id (open_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='抖音账号表';

-- ========================================
-- 3. 抖音视频表
-- ========================================
CREATE TABLE IF NOT EXISTS douyin_video (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '视频ID',
    account_id BIGINT NOT NULL COMMENT '所属账号ID',
    item_id VARCHAR(100) NOT NULL COMMENT '抖音视频ID',
    title VARCHAR(500) COMMENT '视频标题',
    cover_url VARCHAR(500) COMMENT '封面URL',
    video_url VARCHAR(500) COMMENT '视频URL',
    duration INT DEFAULT 0 COMMENT '视频时长(秒)',
    play_count BIGINT DEFAULT 0 COMMENT '播放量',
    like_count BIGINT DEFAULT 0 COMMENT '点赞数',
    comment_count BIGINT DEFAULT 0 COMMENT '评论数',
    share_count BIGINT DEFAULT 0 COMMENT '分享数',
    publish_time DATETIME COMMENT '发布时间',
    status TINYINT DEFAULT 1 COMMENT '状态：0-已删除，1-正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_account_id (account_id),
    INDEX idx_item_id (item_id),
    INDEX idx_publish_time (publish_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='抖音视频表';

-- ========================================
-- 4. DOU+投放任务表（核心表）
-- ========================================
CREATE TABLE IF NOT EXISTS douplus_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    user_id BIGINT NOT NULL COMMENT '创建用户ID',
    account_id BIGINT NOT NULL COMMENT '抖音账号ID',
    video_id BIGINT COMMENT '视频ID（关联douyin_video）',
    item_id VARCHAR(100) COMMENT '抖音视频ID',
    task_type TINYINT DEFAULT 1 COMMENT '任务类型：1-视频投放，2-直播投放',
    target_type TINYINT DEFAULT 1 COMMENT '投放目标：1-系统智能推荐，2-自定义定向',
    duration INT DEFAULT 24 COMMENT '投放时长(小时)',
    budget DECIMAL(10,2) NOT NULL COMMENT '投放预算(元)',
    actual_cost DECIMAL(10,2) DEFAULT 0.00 COMMENT '实际消耗',
    expected_exposure INT DEFAULT 0 COMMENT '预计曝光量',
    actual_exposure INT DEFAULT 0 COMMENT '实际曝光量',
    status VARCHAR(20) DEFAULT 'WAIT' COMMENT '状态：WAIT-待执行，RUNNING-执行中，SUCCESS-成功，FAIL-失败，CANCELLED-已取消',
    order_id VARCHAR(100) COMMENT '抖音订单ID',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry INT DEFAULT 3 COMMENT '最大重试次数',
    error_msg TEXT COMMENT '错误信息',
    scheduled_time DATETIME COMMENT '计划执行时间',
    executed_time DATETIME COMMENT '实际执行时间',
    completed_time DATETIME COMMENT '完成时间',
    target_config TEXT COMMENT '定向配置(JSON)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_user_id (user_id),
    INDEX idx_account_id (account_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DOU+投放任务表';

-- ========================================
-- 5. DOU+投放模板表
-- ========================================
CREATE TABLE IF NOT EXISTS douplus_template (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '模板ID',
    user_id BIGINT NOT NULL COMMENT '创建用户ID',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    task_type TINYINT DEFAULT 1 COMMENT '任务类型',
    target_type TINYINT DEFAULT 1 COMMENT '投放目标',
    duration INT DEFAULT 24 COMMENT '投放时长',
    budget DECIMAL(10,2) COMMENT '默认预算',
    target_config TEXT COMMENT '定向配置(JSON)',
    is_default TINYINT DEFAULT 0 COMMENT '是否默认模板',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DOU+投放模板表';

-- ========================================
-- 6. 评论表
-- ========================================
CREATE TABLE IF NOT EXISTS douyin_comment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '评论ID',
    account_id BIGINT NOT NULL COMMENT '账号ID',
    video_id BIGINT COMMENT '视频ID',
    item_id VARCHAR(100) COMMENT '抖音视频ID',
    comment_id VARCHAR(100) NOT NULL COMMENT '抖音评论ID',
    content TEXT COMMENT '评论内容',
    nickname VARCHAR(100) COMMENT '评论者昵称',
    avatar VARCHAR(500) COMMENT '评论者头像',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    reply_count INT DEFAULT 0 COMMENT '回复数',
    is_top TINYINT DEFAULT 0 COMMENT '是否置顶',
    status TINYINT DEFAULT 1 COMMENT '状态：0-已删除，1-正常，2-待删除',
    is_negative TINYINT DEFAULT 0 COMMENT '是否负面评论',
    keyword_hit VARCHAR(200) COMMENT '命中的关键词',
    comment_time DATETIME COMMENT '评论时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_account_id (account_id),
    INDEX idx_video_id (video_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_status (status),
    INDEX idx_is_negative (is_negative)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';

-- ========================================
-- 7. 敏感词/黑名单表
-- ========================================
CREATE TABLE IF NOT EXISTS keyword_blacklist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    keyword VARCHAR(100) NOT NULL COMMENT '关键词',
    type TINYINT DEFAULT 1 COMMENT '类型：1-敏感词，2-用户黑名单',
    auto_delete TINYINT DEFAULT 1 COMMENT '是否自动删除',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    deleted INT DEFAULT 0 COMMENT '删除标记',
    INDEX idx_user_id (user_id),
    INDEX idx_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='敏感词/黑名单表';

-- ========================================
-- 8. 操作日志表
-- ========================================
CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id BIGINT COMMENT '操作用户ID',
    username VARCHAR(50) COMMENT '操作用户名',
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) COMMENT '模块',
    target_type VARCHAR(50) COMMENT '目标类型',
    target_id VARCHAR(100) COMMENT '目标ID',
    content TEXT COMMENT '操作内容',
    ip VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(500) COMMENT 'UserAgent',
    result TINYINT DEFAULT 1 COMMENT '结果：0-失败，1-成功',
    error_msg TEXT COMMENT '错误信息',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ========================================
-- 9. 数据统计日报表
-- ========================================
CREATE TABLE IF NOT EXISTS stats_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    account_id BIGINT COMMENT '账号ID（可为空表示汇总）',
    stat_date DATE NOT NULL COMMENT '统计日期',
    total_cost DECIMAL(12,2) DEFAULT 0.00 COMMENT '总消耗',
    total_tasks INT DEFAULT 0 COMMENT '投放任务数',
    success_tasks INT DEFAULT 0 COMMENT '成功任务数',
    fail_tasks INT DEFAULT 0 COMMENT '失败任务数',
    total_exposure BIGINT DEFAULT 0 COMMENT '总曝光量',
    total_play BIGINT DEFAULT 0 COMMENT '总播放量',
    total_like BIGINT DEFAULT 0 COMMENT '总点赞数',
    total_comment BIGINT DEFAULT 0 COMMENT '总评论数',
    total_share BIGINT DEFAULT 0 COMMENT '总分享数',
    new_fans INT DEFAULT 0 COMMENT '新增粉丝',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_account_date (user_id, account_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据统计日报表';

-- ========================================
-- 10. 系统配置表
-- ========================================
CREATE TABLE IF NOT EXISTS sys_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '值类型',
    description VARCHAR(255) COMMENT '描述',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 初始化系统配置
INSERT INTO sys_config (config_key, config_value, description) VALUES 
('douyin_client_key', '', '抖音ClientKey'),
('douyin_client_secret', '', '抖音ClientSecret'),
('daily_invest_limit', '10000', '每日投放限额'),
('max_single_invest', '5000', '单次最大投放金额'),
('comment_sync_interval', '120', '评论同步间隔(秒)'),
('task_execute_interval', '5', '任务执行检查间隔(秒)');
