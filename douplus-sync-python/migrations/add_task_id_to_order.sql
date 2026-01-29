-- 添加task_id字段到douplus_order表
-- task_id是DOU+后台显示的订单号（PC端可见）
-- order_id是系统内部订单ID（API返回）

ALTER TABLE `douplus_order` 
ADD COLUMN `task_id` VARCHAR(64) NULL COMMENT 'DOU+后台订单号(PC端可见)' AFTER `order_id`,
ADD INDEX `idx_task_id` (`task_id`);
