# 指标数据不一致问题诊断报告

## 问题描述
前端显示的订单数据与DOU+后台不一致：
- 我们系统：消耗52.29元，播放量21815
- DOU+后台：消耗15.7元，播放量12401

## 根本原因

### 1. 预聚合逻辑错误（已修复）
**问题**：`douplus_order_agg`表使用`SUM()`累加所有历史效果数据

**影响**：导致数据虚高（52.29元是21条记录的累加）

**原因**：抖音API返回的效果数据是**全量累计值**，不是增量！每次调用返回的都是从订单创建到当前时间的总计数据。

**修复**：修改`app/tasks/order_agg.py`
```python
# 错误的聚合方式
SUM(s.stat_cost) as total_cost

# 正确的方式：取最新值
SELECT s.stat_cost as total_cost
FROM douplus_order_stats s
INNER JOIN (
    SELECT order_id, MAX(stat_time) as max_stat_time
    FROM douplus_order_stats
    GROUP BY order_id
) latest ON s.order_id = latest.order_id AND s.stat_time = latest.max_stat_time
```

### 2. Token过期导致效果数据同步停止（未修复）
**问题**：账号5 (AH组-A1) 的access_token在18:13过期

**影响**：
- 效果数据从18:11之后停止更新（已105分钟未同步）
- 定时任务正常执行，但API调用全部失败
- 数据库中最新数据停留在18:10，而DOU+后台显示的是实时数据

**Token过期时间**：2026-01-28 18:13:57

**当前数据状态**：
- 数据库最新数据：18:10（消耗9.52元，播放量5336）
- DOU+后台数据：19:57时查看（消耗15.7元，播放量12401）
- 差异：约100分钟的数据未同步

**需要的操作**：在前端重新授权绑定账号5 (AH组-A1)

## 数据对比

### 修复预聚合后的对比
```
指标          DOU+后台    系统数据(18:10)   差异
消耗(元)      15.70       9.52            -6.18 (100分钟未同步)
播放量        12401       5336            -7065
点赞          52          19              -33
分享          1752        750             -1002
转化          4           2               -2
```

## 已修复的问题

✓ **预聚合逻辑**：从SUM累加改为取最新值
- 修改文件：`/opt/douplus/douplus-sync-python/app/tasks/order_agg.py`
- 更新订单数：29945个
- 影响范围：所有历史订单数据已修正

## 待处理的问题

❌ **Token自动刷新失败**
- 账号5 (AH组-A1) 在18:13过期
- Token自动刷新功能昨天已修复，但本次过期发生在修复之前
- refresh_token也已过期（有效期约30天）
- 需要在前端重新授权

## 技术细节

### 抖音效果数据API的语义
抖音`/open/v3.0/douplus/order/report/`接口返回的数据是**全量累计**：
- `stat_cost`: 订单创建到当前的累计消耗
- `total_play`: 订单创建到当前的累计播放量
- `dp_target_convert_cnt`: 订单创建到当前的累计转化量

### 正确的聚合逻辑
```sql
-- 每个订单只取stat_time最大的那条记录
SELECT order_id, MAX(stat_time) as max_stat_time
FROM douplus_order_stats
GROUP BY order_id

-- 使用最新值，不是SUM()
SELECT s.stat_cost, s.total_play, s.dp_target_convert_cnt
FROM douplus_order_stats s
WHERE s.stat_time = (SELECT MAX(stat_time) FROM douplus_order_stats WHERE order_id = s.order_id)
```

### Celery定时任务配置
效果数据应该每5分钟同步一次：
```python
'sync-stats': {
    'task': 'app.tasks.stats_sync.sync_all_accounts_stats',
    'schedule': crontab(minute='1-59/5'),  # 1,6,11,16,21...
}
```

## 建议措施

1. **立即**：在前端重新授权账号5 (AH组-A1)
2. **验证**：授权后手动触发一次效果数据同步，验证数据是否更新
3. **监控**：设置告警，当效果数据超过10分钟未更新时发送通知
4. **预防**：Token自动刷新功能已修复（每天凌晨2点执行），后续应该不会再发生此类问题

## 相关文件

- `/opt/douplus/douplus-sync-python/app/tasks/order_agg.py` - 订单预聚合逻辑（已修复）
- `/opt/douplus/douplus-sync-python/app/tasks/stats_sync.py` - 效果数据同步
- `/opt/douplus/douplus-sync-python/app/tasks/token_refresh.py` - Token自动刷新
- `/opt/douplus/douplus-sync-python/celery_app.py` - Celery定时任务配置

## 测试脚本

```bash
# 检查数据一致性
python3 /opt/douplus/check_data_consistency.py

# 检查同步状态
python3 /opt/douplus/check_recent_stats_sync.py

# 查询订单所属账号
python3 /opt/douplus/check_order_account.py

# 手动触发预聚合
python3 /opt/douplus/trigger_order_agg.py

# 手动同步效果数据（需要token有效）
python3 /opt/douplus/trigger_stats_sync.py
```

---

**时间**: 2026-01-28 19:57  
**状态**: 预聚合逻辑已修复，等待Token重新授权后验证
