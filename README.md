# DOU+投放管理系统

一个功能完善的抖音DOU+投放管理系统，支持视频投放、评论管理、账号管理等功能。

## 技术栈

### 后端
- Python 3.8+
- Flask 2.3
- SQLAlchemy 2.0
- Celery（异步任务）
- Redis
- MySQL 8

### 前端
- Vue 3
- TypeScript
- Element Plus
- Vite
- Pinia
- ECharts

### 基础设施
- Nginx

## 功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| 登录认证 | JWT认证、投放密码 | ✅ 正常 |
| 账号管理 | 抖音OAuth授权、Token加密存储、自动刷新 | ✅ 正常 |
| DOU+投放 | 单个/批量投放、异步任务队列、自动重试 | ✅ 正常 |
| **订单同步** | **历史订单全量同步、订单数据采集** | **🔒 已冻结** |
| **效果数据** | **订单效果数据同步、单账号手动刷新** | **🔒 已冻结** |
| 评论管理 | 评论同步、敏感词过滤、自动删除、黑名单 | ✅ 正常 |
| 数据统计 | 消耗统计、曝光数据、视频排行榜 | ✅ 正常 |

## 🔒 冻结模块说明

### 订单同步与效果数据采集（已冻结）

以下模块已经过充分测试并稳定运行，**未经特别批准不得修改**：

**核心功能：**
1. **历史订单同步**
   - 分页获取所有历史订单（无时间限制）
   - 订单ID与抖音后台完全一致
   - 支持账号重绑后的数据迁移

2. **效果数据同步**
   - 按订单ID批量查询（每批100个）
   - stat_time覆盖整月，避免漏数据
   - 自动处理API分页

3. **单账号手动刷新**
   - 前端"刷新效果数据"按钮
   - 实时同步指定账号的效果数据
   - 支持投放期间分钟级刷新

**关键文件：**
- `/opt/douplus/douplus-sync-python/app/tasks/order_sync.py` - 订单同步逻辑
- `/opt/douplus/douplus-sync-python/app/tasks/stats_sync.py` - 效果数据同步逻辑
- `/opt/douplus/douplus-sync-python/app/api/stats_api.py` - 效果数据API
- `/opt/douplus/douplus-web/src/views/douplus/Records.vue` - 前端页面
- `/opt/douplus/douplus-web/src/components/order/OrderListView.vue` - 订单列表组件

**技术要点：**
- 订单ID直接从API获取，保证与后台一致
- 使用`filter.order_ids`参数替代时间范围查询
- `memberId`字段映射到`accountId`参数
- 前端通过`defineExpose`暴露`filters`对象

## 项目结构

```
douplus/
├── nginx.conf                  # Nginx反向代理配置
├── douplus-sync-python/        # 后端项目（Python）
│   ├── api_server.py           # Flask API服务入口
│   ├── celery_app.py           # Celery异步任务配置
│   ├── requirements.txt        # Python依赖
│   └── app/
│       ├── config.py           # 配置文件
│       ├── models.py           # 数据库模型
│       ├── douyin_client.py    # 抖音API客户端
│       ├── api/                # API路由
│       │   ├── sync_api.py     # 🔒订单同步API（已冻结）
│       │   └── stats_api.py    # 🔒效果数据API（已冻结）
│       └── tasks/              # 异步任务
│           ├── order_sync.py   # 🔒订单同步任务（已冻结）
│           └── stats_sync.py   # 🔒效果数据同步任务（已冻结）
└── douplus-web/                # 前端项目
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.ts
        ├── App.vue
        ├── api/                # API接口封装
        ├── router/             # 路由配置
        ├── stores/             # Pinia状态管理
        ├── components/         # 公共组件
        │   └── order/
        │       └── OrderListView.vue  # 🔒订单列表组件（已冻结）
        └── views/              # 页面
            ├── auth/           # 登录页
            ├── dashboard/      # 首页概览
            ├── account/        # 账号管理
            ├── douplus/        # DOU+投放
            │   └── Records.vue # 🔒投放记录页（已冻结）
            └── comment/        # 评论管理
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- MySQL 8.0+
- Redis 7+

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/douplus.git
cd douplus
```

#### 2. 初始化数据库

参考 `douplus-sync-python/app/models.py` 中的数据库模型

#### 3. 修改配置

编辑 `douplus-sync-python/app/config.py`：

```python
class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "douplus"
    DB_USER: str = "douplus"
    DB_PASSWORD: str = ""
    
    # Redis配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
```

#### 4. 启动后端

```bash
cd douplus-sync-python
pip install -r requirements.txt
python3 api_server.py
```

后端服务将在 `http://localhost:5000` 启动

#### 5. 启动Celery Worker（可选）

```bash
cd douplus-sync-python
celery -A celery_app worker --loglevel=info
```

#### 6. 启动前端

```bash
cd douplus-web
npm install
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 生产部署

1. 构建前端

```bash
cd douplus-web
npm run build
```

2. 启动Flask服务

```bash
cd douplus-sync-python
nohup python3 api_server.py > logs/flask.log 2>&1 &
```

3. 启动Celery Worker

```bash
cd douplus-sync-python
nohup celery -A celery_app worker --loglevel=info > logs/celery.log 2>&1 &
```

## 默认账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

## API文档

### 认证相关

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/auth/info | GET | 获取当前用户信息 |
| /api/auth/password | POST | 修改密码 |
| /api/auth/invest-password | POST | 设置投放密码 |

### 账号管理

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/account/list | GET | 获取账号列表 |
| /api/account/{id} | GET | 获取账号详情 |
| /api/account/{id}/daily-limit | PUT | 更新日限额 |
| /api/account/{id} | DELETE | 解绑账号 |

### DOU+投放

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/douplus/task/create | POST | 创建投放任务 |
| /api/douplus/task/page | GET | 分页查询投放记录 |
| /api/douplus/task/{id}/cancel | POST | 取消任务 |

### 评论管理

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/comment/page | GET | 分页查询评论 |
| /api/comment/{id}/delete | POST | 标记删除评论 |
| /api/comment/keyword/list | GET | 获取敏感词列表 |
| /api/comment/keyword/add | POST | 添加敏感词 |

## 核心设计

### 🔒 订单同步流程（已冻结）

```
用户点击"同步历史订单"
    ↓
创建同步任务（DB）
    ↓
Celery异步执行
    ↓
分页调用抖音订单列表API
    ↓
保存订单到数据库
    ↓
更新任务状态
```

### 🔒 效果数据同步流程（已冻结）

```
定时任务（每5分钟）或手动触发
    ↓
获取账号的所有订单
    ↓
按订单ID批量查询效果数据（每批100个）
    ↓
使用filter.order_ids参数
    ↓
stat_time覆盖整月
    ↓
保存效果数据到数据库
```

### Token安全

- 所有抖音Token使用AES加密存储
- 自动检测即将过期的Token并刷新
- Token永不明文传输或日志输出

## 开发计划

- [x] 基础架构搭建
- [x] 登录认证
- [x] 账号管理
- [x] DOU+投放核心
- [x] 🔒 **订单同步（已冻结）**
- [x] 🔒 **效果数据同步（已冻结）**
- [x] 评论管理
- [x] 数据统计看板
- [ ] 抖音Webhook接入
- [ ] 投放效果分析
- [ ] 多用户权限管理

## 维护说明

### 🔒 冻结模块修改流程

对于标记为 🔒 的冻结模块（订单同步、效果数据同步），如需修改需遵循以下流程：

1. **特别批准**：向项目负责人提交变更申请，说明修改原因和影响范围
2. **充分测试**：在测试环境完成全面测试
3. **备份验证**：备份现有代码和数据
4. **逐步部署**：先在单个账号测试，确认无误后再全量部署
5. **监控告警**：部署后持续监控日志和数据准确性

**冻结原因**：这些模块已经稳定运行，订单ID与后台一致，效果数据同步准确。任何修改都可能导致数据不一致或同步异常。

## License

MIT License
