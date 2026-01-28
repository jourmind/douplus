-- 创建订单维度预聚合表
-- 用途：存储每个订单的聚合指标，避免查询时多层JOIN和实时计算
-- 更新频率：每次效果数据同步后更新

CREATE TABLE IF NOT EXISTS `douplus_order_agg` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `order_id` varchar(64) NOT NULL COMMENT '订单ID',
  `item_id` varchar(64) NOT NULL COMMENT '视频ID',
  `account_id` bigint(20) NOT NULL COMMENT '账号ID',
  
  -- 原始指标（从douplus_order_stats聚合）
  `total_cost` decimal(10,2) DEFAULT '0.00' COMMENT '总消耗(元)',
  `total_play` int(11) DEFAULT '0' COMMENT '总播放量',
  `total_like` int(11) DEFAULT '0' COMMENT '总点赞数',
  `total_comment` int(11) DEFAULT '0' COMMENT '总评论数',
  `total_share` int(11) DEFAULT '0' COMMENT '总转发数',
  `total_follow` int(11) DEFAULT '0' COMMENT '总关注数',
  `total_convert` int(11) DEFAULT '0' COMMENT '总转化数',
  `play_duration_5s` float DEFAULT '0' COMMENT '5秒完播率(0-1之间的小数)',
  
  -- 预聚合计算指标
  `play_per_100_cost` decimal(10,2) DEFAULT '0.00' COMMENT '百播放量 = 播放量/消耗*100',
  `avg_convert_cost` decimal(10,2) DEFAULT NULL COMMENT '转化成本 = 消耗/转化数(元,可为NULL)',
  `share_rate` decimal(10,4) DEFAULT '0.0000' COMMENT '百转发率 = 转发/播放*100',
  `like_rate` decimal(10,4) DEFAULT '0.0000' COMMENT '点赞比 = 点赞/播放',
  `follow_rate` decimal(10,4) DEFAULT '0.0000' COMMENT '转发比 = 转发/播放',
  
  -- 时间戳
  `stat_time` datetime NOT NULL COMMENT '最后统计时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_id` (`order_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_item_id` (`item_id`),
  KEY `idx_stat_time` (`stat_time`),
  
  -- 排序优化索引
  KEY `idx_play_per_100_cost` (`play_per_100_cost`),
  KEY `idx_avg_convert_cost` (`avg_convert_cost`),
  KEY `idx_total_cost` (`total_cost`),
  KEY `idx_total_play` (`total_play`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DOU+订单聚合表(预聚合)';
