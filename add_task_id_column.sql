-- 添加task_id字段到douplus_order表
ALTER TABLE douplus_order ADD COLUMN task_id VARCHAR(64) NULL AFTER order_id;
ALTER TABLE douplus_order ADD INDEX idx_task_id (task_id);

-- 注释说明
-- task_id: 抖音任务ID，续费API需要使用此ID
-- order_id: 抖音订单ID，用于订单查询和展示
