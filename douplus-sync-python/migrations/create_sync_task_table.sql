-- 同步任务记录表
CREATE TABLE IF NOT EXISTS `sync_task_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `task_type` varchar(20) NOT NULL COMMENT '任务类型：order(订单同步) / stats(效果同步)',
  `sync_mode` varchar(20) DEFAULT NULL COMMENT '同步模式：full(全量) / incremental(增量)',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/running/completed/failed',
  `total_accounts` int DEFAULT 0 COMMENT '总账号数',
  `completed_accounts` int DEFAULT 0 COMMENT '已完成账号数',
  `total_records` int DEFAULT 0 COMMENT '总同步记录数',
  `success_count` int DEFAULT 0 COMMENT '成功数量',
  `fail_count` int DEFAULT 0 COMMENT '失败数量',
  `error_message` text COMMENT '错误信息',
  `start_time` datetime DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `celery_task_id` varchar(255) DEFAULT NULL COMMENT 'Celery任务ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_celery_task_id` (`celery_task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步任务日志表';

-- 同步任务明细表（可选，记录每个账号的同步详情）
CREATE TABLE IF NOT EXISTS `sync_task_detail` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id` bigint NOT NULL COMMENT '任务ID（关联sync_task_log）',
  `account_id` bigint NOT NULL COMMENT '账号ID',
  `account_name` varchar(100) DEFAULT NULL COMMENT '账号名称',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/running/completed/failed',
  `record_count` int DEFAULT 0 COMMENT '同步记录数',
  `error_message` text COMMENT '错误信息',
  `start_time` datetime DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步任务明细表';
