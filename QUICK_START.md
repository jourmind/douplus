# DOU+订单管理系统 - 快速启动指南

## ⚡ 一键启动

```bash
bash /opt/douplus/start_services.sh
```

这个脚本会：
- ✅ 自动检测并启动所有必需服务
- ✅ 验证服务健康状态
- ✅ 显示详细的服务信息
- ✅ 提供失败诊断建议

---

## 📋 常用命令

| 命令 | 说明 |
|------|------|
| `bash /opt/douplus/start_services.sh` | **启动所有服务** |
| `bash /opt/douplus/check_services.sh` | 查看服务状态 |
| `bash /opt/douplus/stop_services.sh` | 停止所有服务 |
| `bash /opt/douplus/restart_services.sh` | 重启所有服务 |

---

## 🔍 服务说明

系统运行需要以下3个服务：

1. **Flask API Server** (端口5000) - 处理HTTP请求
2. **Celery Worker** (后台任务) - 执行订单同步
3. **Celery Beat** (定时调度) - 每5分钟自动同步

---

## 📖 详细文档

完整的使用说明和故障排查指南：[SERVICE_MANAGEMENT.md](SERVICE_MANAGEMENT.md)

---

## 🚨 常见问题

**Q: 服务器重启后需要手动启动服务吗？**  
A: 是的，目前需要手动运行 `bash /opt/douplus/start_services.sh`

**Q: 如何确认服务正常运行？**  
A: 运行 `bash /opt/douplus/check_services.sh` 查看状态

**Q: 代码更新后需要重启吗？**  
A: 是的，运行 `bash /opt/douplus/restart_services.sh`

---

**版本**: 1.0 | **最后更新**: 2026-01-29
