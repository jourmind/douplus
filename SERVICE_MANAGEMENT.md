# DOU+订单管理系统 - 服务管理脚本使用说明

## 📋 系统服务组成

DOU+订单管理系统由以下3个核心服务组成：

| 服务 | 作用 | 端口/进程 |
|------|------|----------|
| **Flask API Server** | 提供HTTP API接口，处理前端请求 | 端口 5000 |
| **Celery Worker** | 执行后台任务（订单同步、效果数据同步等） | 多进程 |
| **Celery Beat** | 定时任务调度器，每5分钟触发同步 | 单进程 |

---

## 🚀 快速使用

### 1. 启动所有服务

```bash
bash /opt/douplus/start_services.sh
```

**功能**：
- 自动检测服务是否已运行
- 启动未运行的服务
- 验证服务健康状态
- 显示服务摘要和管理命令

**输出示例**：
```
========================================
DOU+订单管理系统 - 服务启动
========================================

[1/3] 检查 Flask API 服务...
✓ Flask API 已运行 (PID: 12345)
✓ API 响应正常 (HTTP 401)

[2/3] 检查 Celery Worker...
✓ Celery Worker 已运行 (5 个进程)

[3/3] 检查 Celery Beat...
✓ Celery Beat 已运行 (PID: 12346)

✓ 所有服务启动完成
```

---

### 2. 查看服务状态

```bash
bash /opt/douplus/check_services.sh
```

**输出示例**：
```
========================================
DOU+订单管理系统 - 服务状态
========================================

Flask API:      ✓ 运行中 (PID: 12345, HTTP: 401)
Celery Worker:  ✓ 运行中 (5 个进程)
Celery Beat:    ✓ 运行中 (PID: 12346)
```

---

### 3. 停止所有服务

```bash
bash /opt/douplus/stop_services.sh
```

**功能**：
- 安全停止所有服务
- 显示停止结果

---

### 4. 重启所有服务

```bash
bash /opt/douplus/restart_services.sh
```

**功能**：
- 依次停止所有服务
- 等待3秒
- 重新启动所有服务

**使用场景**：
- 代码更新后需要重启
- 服务出现异常需要重启
- 配置文件修改后生效

---

## 🔧 故障排查

### 问题1：Flask API 启动失败

**诊断信息**：
```
1. 检查端口5000是否被占用: sudo netstat -tlnp | grep 5000
2. 查看错误日志: tail -50 /opt/douplus/douplus-sync-python/logs/api_server.log
3. 检查Python环境: python3 --version
4. 检查依赖安装: pip3 list | grep -E '(flask|sqlalchemy)'
```

**解决方案**：
- 如果端口被占用，停止占用进程或修改配置端口
- 查看日志中的具体错误信息
- 确保Python 3.8+版本
- 重新安装依赖：`pip3 install -r requirements.txt`

---

### 问题2：Celery Worker 启动失败

**诊断信息**：
```
1. 检查Redis连接: redis-cli ping
2. 查看错误日志: tail -50 /opt/douplus/douplus-sync-python/logs/celery_worker.log
3. 检查Celery安装: pip3 show celery
4. 手动启动测试: cd /opt/douplus/douplus-sync-python && celery -A celery_app worker --loglevel=info
```

**解决方案**：
- 确保Redis服务运行中：`sudo systemctl status redis`
- 如果Redis未安装：`sudo apt install redis-server`
- 检查Redis配置：`/etc/redis/redis.conf`
- 查看日志中的详细错误

---

### 问题3：Celery Beat 启动失败

**诊断信息**：
```
1. 查看错误日志: tail -50 /opt/douplus/douplus-sync-python/logs/beat.log
2. 检查PID文件: ls -lh /opt/douplus/douplus-sync-python/logs/beat.pid
3. 手动启动测试: cd /opt/douplus/douplus-sync-python && celery -A celery_app beat --loglevel=info
```

**解决方案**：
- 清理旧的PID文件：`rm -f /opt/douplus/douplus-sync-python/logs/beat.pid`
- 重新启动服务

---

## 📊 日志查看

### 实时查看API日志
```bash
tail -f /opt/douplus/douplus-sync-python/logs/api_server.log
```

### 实时查看Worker日志
```bash
tail -f /opt/douplus/douplus-sync-python/logs/celery_worker.log
```

### 实时查看Beat日志
```bash
tail -f /opt/douplus/douplus-sync-python/logs/beat.log
```

### 查看最近50行错误
```bash
tail -50 /opt/douplus/douplus-sync-python/logs/api_server.log | grep ERROR
```

---

## ⏰ 定时任务说明

系统会自动执行以下定时任务：

| 任务 | 执行时间 | 说明 |
|------|---------|------|
| 增量同步订单 | 每5分钟 (1,6,11,16,21...) | 同步最近7天有更新的订单 |
| 同步效果数据 | 每5分钟 (1,6,11,16,21...) | 同步订单的效果数据（播放、点赞等） |
| 聚合视频数据 | 每5分钟 (2,7,12,17,22...) | 预聚合视频维度的统计数据 |
| 自动刷新Token | 每天凌晨2点 | 刷新即将过期的access_token |

---

## 🎯 最佳实践

### 服务器重启后的操作

1. 检查服务状态
```bash
bash /opt/douplus/check_services.sh
```

2. 如果服务未运行，启动服务
```bash
bash /opt/douplus/start_services.sh
```

### 代码更新后的操作

1. 拉取最新代码
```bash
cd /opt/douplus
git pull
```

2. 重启服务
```bash
bash /opt/douplus/restart_services.sh
```

### 定期检查

建议每周检查一次服务状态和日志：
```bash
# 检查服务状态
bash /opt/douplus/check_services.sh

# 检查最近的错误日志
tail -100 /opt/douplus/douplus-sync-python/logs/api_server.log | grep ERROR
tail -100 /opt/douplus/douplus-sync-python/logs/celery_worker.log | grep ERROR
```

---

## 🔐 安全注意事项

1. **脚本权限**：这些脚本使用`bash`执行，不需要额外的执行权限
2. **日志文件**：定期清理或归档日志文件，避免磁盘空间不足
3. **进程管理**：不要手动kill进程，使用提供的停止脚本

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. 查看完整日志
```bash
cat /opt/douplus/douplus-sync-python/logs/api_server.log
cat /opt/douplus/douplus-sync-python/logs/celery_worker.log
```

2. 检查系统资源
```bash
df -h          # 磁盘空间
free -h        # 内存使用
top            # CPU和进程状态
```

3. 检查网络连接
```bash
curl http://127.0.0.1:5000/api/auth/info
redis-cli ping
```

---

**版本**: 1.0  
**最后更新**: 2026-01-29
