#!/bin/bash
# DOU+ 后端服务启动脚本

cd /opt/douplus/douplus-server

# 数据库配置
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_DATABASE=douplus
export MYSQL_USERNAME=douplus
export MYSQL_PASSWORD=Asd123000

# Redis配置
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=

# 服务端口
export SERVER_PORT=8081

# JWT配置
export JWT_SECRET=douplus-jwt-secret-key-2024-very-long-and-secure-string-256bits
export JWT_EXPIRATION=86400000

# AES密钥
export AES_SECRET_KEY=douplus-aes-secret-key-32char!

# 抖音开放平台OAuth配置
export DOUYIN_APP_ID=1854346912597002
export DOUYIN_APP_SECRET=76962f707eec1dfb0ae30995696b0a9d4c9a437e
export DOUYIN_OAUTH_CALLBACK=https://www.jourmind.com/oauth/douplus.php
export DOUYIN_OAUTH_URL=https://open.oceanengine.com/audit/oauth.html

# 日志级别
export LOG_LEVEL=INFO

# 启动服务
exec java -jar -Xms256m -Xmx512m target/douplus-server-1.0.0.jar
