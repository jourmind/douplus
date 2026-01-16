# DOU+投放管理系统

一个功能完善的抖音DOU+投放管理系统，支持视频投放、评论管理、账号管理等功能。

## 技术栈

### 后端
- Java 17
- Spring Boot 3.2
- MyBatis Plus
- Spring Security + JWT
- Quartz（定时任务）
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
- Docker + Docker Compose
- Nginx

## 功能模块

| 模块 | 功能 |
|------|------|
| 登录认证 | JWT认证、投放密码 |
| 账号管理 | 抖音OAuth授权、Token加密存储、自动刷新 |
| DOU+投放 | 单个/批量投放、异步任务队列、自动重试、风控保护 |
| 评论管理 | 评论同步、敏感词过滤、自动删除、黑名单 |
| 数据统计 | 消耗统计、曝光数据、视频排行榜 |

## 项目结构

```
douplus/
├── docker-compose.yml          # Docker一键部署配置
├── nginx.conf                  # Nginx反向代理配置
├── douplus-server/             # 后端项目
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/
│       ├── java/com/douplus/
│       │   ├── DouplusApplication.java   # 启动类
│       │   ├── auth/                     # 认证模块
│       │   │   ├── controller/
│       │   │   ├── service/
│       │   │   ├── domain/
│       │   │   ├── mapper/
│       │   │   └── security/             # JWT、Security配置
│       │   ├── account/                  # 账号管理模块
│       │   ├── douplus/                  # DOU+投放核心模块
│       │   │   ├── client/               # 抖音API封装
│       │   │   ├── task/                 # 定时任务执行器
│       │   │   ├── controller/
│       │   │   ├── service/
│       │   │   └── domain/
│       │   ├── comment/                  # 评论管理模块
│       │   └── common/                   # 通用工具
│       │       ├── config/
│       │       ├── exception/
│       │       ├── result/
│       │       └── utils/
│       └── resources/
│           ├── application.yml           # 应用配置
│           └── db/init.sql               # 数据库初始化脚本
└── douplus-web/                # 前端项目
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.ts
        ├── App.vue
        ├── api/                          # API接口封装
        ├── router/                       # 路由配置
        ├── stores/                       # Pinia状态管理
        ├── utils/                        # 工具函数
        ├── layouts/                      # 布局组件
        ├── components/                   # 公共组件
        └── views/                        # 页面
            ├── auth/                     # 登录页
            ├── dashboard/                # 首页概览
            ├── account/                  # 账号管理
            ├── douplus/                  # DOU+投放
            └── comment/                  # 评论管理
```

## 快速开始

### 环境要求

- JDK 17+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- Maven 3.8+

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/douplus.git
cd douplus
```

#### 2. 初始化数据库

```bash
# 创建数据库并执行初始化脚本
mysql -u root -p < douplus-server/src/main/resources/db/init.sql
```

#### 3. 修改配置

编辑 `douplus-server/src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/douplus
    username: your_username
    password: your_password
  data:
    redis:
      host: localhost
      port: 6379

# 抖音API配置
douyin:
  api:
    client-key: your_client_key
    client-secret: your_client_secret

# JWT密钥（生产环境请更换）
jwt:
  secret: your-256-bit-secret-key-here
```

#### 4. 启动后端

```bash
cd douplus-server
mvn spring-boot:run
```

后端服务将在 `http://localhost:8080` 启动

#### 5. 启动前端

```bash
cd douplus-web
npm install
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

### Docker部署

#### 一键启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 服务端口

| 服务 | 端口 |
|------|------|
| 前端 (Nginx) | 80 |
| 后端 (Spring Boot) | 8080 |
| MySQL | 3306 |
| Redis | 6379 |

### 生产部署

1. 构建前端

```bash
cd douplus-web
npm run build
```

2. 构建后端

```bash
cd douplus-server
mvn clean package -DskipTests
```

3. 部署JAR包

```bash
java -jar -Xms512m -Xmx1024m douplus-server-1.0.0.jar
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

### 投放任务流程

```
用户提交投放
    ↓
创建投放任务（DB）
    ↓
风控检查（限额、余额）
    ↓
任务入队（状态：WAIT）
    ↓
定时执行器（每5秒）
    ↓
调用抖音DOU+ API
    ↓
更新任务状态（SUCCESS/FAIL）
    ↓
失败自动重试（最多3次）
```

### Token安全

- 所有抖音Token使用AES加密存储
- 自动检测即将过期的Token并刷新
- Token永不明文传输或日志输出

### 风控策略

- 单账号单日限额检查
- 单笔投放金额上限
- 投放密码二次验证
- 操作日志审计

## 开发计划

- [x] 基础架构搭建
- [x] 登录认证
- [x] 账号管理
- [x] DOU+投放核心
- [x] 评论管理
- [x] 数据统计看板
- [ ] 抖音Webhook接入
- [ ] 投放效果分析
- [ ] 多用户权限管理

## License

MIT License
