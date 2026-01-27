#!/bin/bash
# 修复Nginx配置：添加vhost目录include并重新加载

CONFIG_FILE="/www/server/nginx/conf/nginx.conf"
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "修复Nginx配置"
echo "=========================================="

# 备份原配置
echo "1. 备份原配置..."
sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "   备份完成：$BACKUP_FILE"

# 检查是否已经存在include
if grep -q "include /www/server/nginx/conf/vhost/\*.conf;" "$CONFIG_FILE"; then
    echo "2. vhost include已存在，跳过添加"
else
    echo "2. 添加vhost include..."
    sudo sed -i '/include \/www\/server\/panel\/vhost\/nginx\/\*\.conf;/i include \/www\/server\/nginx\/conf\/vhost\/\*\.conf;' "$CONFIG_FILE"
    echo "   添加完成"
fi

# 测试配置
echo "3. 测试Nginx配置..."
sudo nginx -t 2>&1 | tail -5

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "4. 配置测试通过，重新加载Nginx..."
    sudo nginx -s reload
    echo "   ✅ Nginx已重新加载"
    echo ""
    echo "=========================================="
    echo "修复完成！"
    echo "=========================================="
else
    echo "4. ❌ 配置测试失败，恢复备份..."
    sudo cp "$BACKUP_FILE" "$CONFIG_FILE"
    echo "   已恢复原配置"
fi
