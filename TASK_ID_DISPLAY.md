# 订单号和任务ID前端展示修改

## 修改内容

### 1. 后端API修改

#### 修改文件：`app/api/query_api.py`

**第154行和177行**：SELECT语句添加`task_id`字段
```sql
SELECT 
    o.id, o.user_id, o.account_id, o.item_id, o.order_id, o.task_id,
    ...
```

**第232-268行**：数据组装添加`taskId`字段
```python
record = {
    'id': row[0],
    'userId': row[1],
    'accountId': row[2],
    'itemId': item_id,
    'orderId': order_id,
    'taskId': task_id,  # DOU+后台订单号(PC端可见)
    'status': row[6],
    ...
}
```

### 2. 前端展示修改

#### 修改文件：`src/components/order/OrderListView.vue`

**第74-88行**：订单详情弹窗展示两个ID
```vue
<el-descriptions :column="2" border>
  <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
  <el-descriptions-item label="订单号（后台）">{{ currentTask.taskId || '暂无' }}</el-descriptions-item>
  <el-descriptions-item label="订单ID（内部）">{{ currentTask.orderId }}</el-descriptions-item>
  ...
</el-descriptions>
```

## 字段说明

| 字段名 | 含义 | 用途 |
|-------|------|------|
| **taskId** | DOU+后台订单号（PC端可见） | 用户在DOU+后台看到的订单号，用于与后台数据对应 |
| **orderId** | 系统内部订单ID | API返回的唯一标识，用于内部查询和链路追踪 |
| **id** | 任务记录ID | 数据库表的自增主键 |

## 展示效果

用户点击订单详情时，会看到：

```
任务ID: 12345
订单号（后台）: 1855548567381076    ← DOU+后台可见
订单ID（内部）: 1855548567381092    ← 系统内部ID
视频ID: 7600074706619878683
...
```

## 数据覆盖率

- 最近200条订单已有`taskId`数据
- 历史订单需要等待下次同步时自动更新
- 如果`taskId`为空，展示"暂无"

## 部署状态

- ✅ 后端API修改完成
- ✅ 前端代码修改完成
- ✅ 前端构建完成（17.95s）
- ✅ 后端服务重启（进程: 3805906）

## 使用建议

1. **优先展示taskId**：因为这是用户在DOU+后台看到的订单号
2. **搜索功能**：后续可以同时支持`orderId`和`taskId`搜索
3. **导出功能**：建议同时导出两个ID，方便用户核对
