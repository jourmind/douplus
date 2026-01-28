# 订单数据导出功能说明

## 功能概述

订单数据导出功能允许用户将订单列表数据导出为Excel文件，支持按当前筛选条件导出。

## 导出位置

### 1. 投放记录页面 (Records.vue)
- 位置：页面顶部筛选器右侧的"数据导出"按钮
- 支持筛选条件：
  - 订单状态（未支付、审核中、投放中等）
  - 账号筛选
  - 视频标题关键词搜索
  - 下单时间范围

### 2. 历史记录页面 (History.vue)
- 位置：页面顶部筛选器右侧的"数据导出"按钮
- 支持筛选条件：
  - 订单状态
  - 账号筛选
  - 视频标题关键词搜索
  - 下单时间范围

## 导出内容

Excel文件包含以下字段：

### 基础信息
- 订单ID
- 视频ID
- 状态（中文显示）
- 预算（元）
- 视频标题
- 账号名称
- 下单时间

### 效果数据
- 实际消耗（元）
- 播放量
- 点赞数
- 评论数
- 转发数
- 关注数
- 转化数

### 计算指标
- 百播放量（播放量/消耗×100）
- 转化成本（消耗/转化数）
- 百转发率（转发/播放×100）
- 5秒完播率（百分比）

## 导出限制

- 单次导出最多10,000条记录
- 文件格式：.xlsx（Excel 2007+）
- 文件名格式：`订单数据_YYYYMMDD_HHMMSS.xlsx`

## 技术实现

### 后端API
- **路径**: `/api/douplus/task/export`
- **方法**: GET
- **认证**: 需要Bearer Token
- **依赖**: openpyxl库
- **实现**: [export_api.py](../douplus-sync-python/app/api/export_api.py)

### 前端实现
- **API函数**: `exportTaskData()` in [douplus.ts](../douplus-web/src/api/douplus.ts)
- **Records页面**: `handleExportData()` in [Records.vue](../douplus-web/src/views/douplus/Records.vue)
- **History页面**: `exportData()` in [History.vue](../douplus-web/src/views/douplus/History.vue)

### 数据来源
- 从订单预聚合表（`douplus_order_agg`）读取效果数据
- 使用预计算的指标，无需实时计算
- 查询性能优化，单次JOIN即可获取所有数据

## 状态映射

| 数据库状态 | Excel显示 |
|-----------|----------|
| UNPAID | 未支付 |
| AUDITING | 审核中 |
| DELIVERING | 投放中 |
| DELIVERIED | 已完成 |
| UNDELIVERIED | 投放终止 |
| AUDIT_PAUSE | 审核暂停 |
| AUDIT_REJECTED | 审核不通过 |

## 测试

运行测试脚本验证导出功能：

```bash
cd /opt/douplus
python3 test_export_api.py
```

测试覆盖：
- ✅ 全量导出
- ✅ 按状态筛选导出
- ✅ 按关键词筛选导出
- ✅ 按时间范围筛选导出
- ✅ 文件下载和保存

## 浏览器使用

1. 在投放记录或历史记录页面
2. 设置需要的筛选条件（可选）
3. 点击"数据导出"按钮
4. 等待提示"正在导出数据，请稍候..."
5. 导出完成后，浏览器自动下载Excel文件
6. 成功提示："导出成功"

## 注意事项

1. **性能考虑**：导出大量数据（>1000条）时可能需要等待几秒钟
2. **数据时效性**：导出的是当前时刻的数据快照
3. **中文文件名**：使用UTF-8编码，确保各浏览器兼容
4. **空值处理**：
   - 转化成本为NULL时显示为0
   - 空字符串显示为空白单元格
5. **数值格式**：
   - 金额保留2位小数
   - 百分比保留4位小数
   - 整数不含小数点

## 错误处理

- 导出失败时显示错误提示
- 后端错误记录在日志：`/opt/douplus/douplus-sync-python/logs/api_server.log`
- 前端错误显示在浏览器控制台

## 未来优化方向

1. 支持自定义导出字段
2. 支持导出为CSV格式
3. 添加导出进度条（大数据量时）
4. 支持批量导出多个账号的数据
5. 添加导出历史记录
