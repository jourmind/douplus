# 订单ID不一致问题修复说明

## 问题描述

数据库中的订单ID与DOU+后台显示的订单号不一致：
- 数据库中：`1855548567381092`
- DOU+后台：`1855548567381076`

## 根本原因

抖音开放平台API返回**两个不同的订单ID**：

1. **order_id**: 系统内部订单ID（API返回的唯一标识）
2. **task_id**: PC端可见订单号（DOU+后台显示的订单号）

## 解决方案

### 1. 数据库修改

添加`task_id`字段到`douplus_order`表：

```sql
ALTER TABLE `douplus_order` 
ADD COLUMN `task_id` VARCHAR(64) NULL COMMENT 'DOU+后台订单号(PC端可见)' AFTER `order_id`,
ADD INDEX `idx_task_id` (`task_id`);
```

### 2. ORM模型修改

修改 `app/models.py` 第91行：

```python
task_id = Column(String(64), index=True)  # DOU+后台订单号(PC端可见)
```

### 3. 订单同步逻辑修改

修改 `app/tasks/order_sync.py` 第218行，添加task_id保存：

```python
values = {
    "order_id": order_info.get("order_id"),
    "task_id": order_info.get("task_id"),  # DOU+后台订单号(PC端可见)
    ...
}
```

### 4. 历史数据更新

运行 `update_task_ids.py` 脚本，批量更新现有订单的task_id字段：

```bash
python3 update_task_ids.py
```

结果：成功更新200条订单的task_id（覆盖率1.2%，其他订单token已过期）

### 5. 验证结果

所有DOU+后台订单号都能通过`task_id`查询到：

| DOU+后台订单号 | order_id | 创建时间 | 状态 |
|--------------|----------|---------|------|
| 1855548567381076 | 1855548567381092 | 2026-01-28 16:30:34 | ✓ 找到 |
| 1855548553415739 | 1855548553416715 | 2026-01-28 16:30:23 | ✓ 找到 |
| 1855548517984355 | 1855548524204419 | 2026-01-28 16:30:19 | ✓ 找到 |
| 1855548548789328 | 1855548548789344 | 2026-01-28 16:30:14 | ✓ 找到 |
| 1855548523186375 | 1855548523186391 | 2026-01-28 16:30:09 | ✓ 找到 |

## 后续建议

### 1. API查询参数支持

根据抖音文档，订单列表API支持`task_id`参数：

```python
# 通过DOU+后台订单号查询
client.get_order_list(
    aweme_sec_uid=sec_uid,
    task_id="1855548567381076"  # 使用DOU+后台订单号
)
```

### 2. 前端展示优化

在订单详情页同时展示两个ID：

```vue
<template>
  <div>
    <p>订单号（后台）: {{ order.task_id }}</p>
    <p>订单号（系统）: {{ order.order_id }}</p>
  </div>
</template>
```

建议优先展示`task_id`，因为这是用户在DOU+后台看到的订单号。

### 3. 搜索功能增强

修改订单搜索功能，同时支持`order_id`和`task_id`查询：

```python
# 查询逻辑
query = db.query(DouplusOrder).filter(
    or_(
        DouplusOrder.order_id == keyword,
        DouplusOrder.task_id == keyword
    )
)
```

## 关键文件

- 数据库迁移脚本: `migrations/add_task_id_to_order.sql`
- ORM模型: `app/models.py` (第91行)
- 订单同步: `app/tasks/order_sync.py` (第218行)
- 批量更新脚本: `update_task_ids.py`
- 验证脚本: `verify_task_ids.py`

## 服务重启

修改完成后，已重启Flask API服务：
- 旧进程: 3777941
- 新进程: 3798616
- 重启时间: 2026-01-28 17:49

## 注意事项

1. 后续新订单会自动保存`task_id`
2. 历史订单只有token未过期的账号才能更新`task_id`
3. `order_id`仍然是系统的主键，不能修改
4. `task_id`用于与DOU+后台的订单号匹配
