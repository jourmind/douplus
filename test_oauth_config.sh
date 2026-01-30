#!/bin/bash
# OAuth配置验证测试脚本

echo "=========================================="
echo "DOU+ OAuth配置验证"
echo "=========================================="
echo ""

echo "1️⃣  检查环境变量配置"
echo "------------------------------------------"
cd /opt/douplus/douplus-sync-python
source load_env.sh
echo "✅ APP_ID: $DOUPLUS_APP_ID"
echo "✅ APP_SECRET: ${DOUPLUS_APP_SECRET:0:10}..."
echo "✅ CALLBACK_URL: $DOUPLUS_CALLBACK_URL"
echo ""

echo "2️⃣  检查PHP回调文件配置"
echo "------------------------------------------"
PHP_FILE="/opt/douplus/douplus-web/dist/oauth/douplus.php"
if [ -f "$PHP_FILE" ]; then
    echo "✅ PHP文件存在: $PHP_FILE"
    echo ""
    echo "配置信息："
    grep "define('APP_ID'" $PHP_FILE
    grep "define('APP_SECRET'" $PHP_FILE
    echo ""
    echo "回调地址注释："
    grep "回调地址:" $PHP_FILE | head -1
    echo ""
    echo "跳转URL："
    grep "window.location.href" $PHP_FILE | head -1
else
    echo "❌ PHP文件不存在: $PHP_FILE"
fi
echo ""

echo "3️⃣  检查Nginx配置"
echo "------------------------------------------"
echo "网站根目录应该指向: /opt/douplus/douplus-web/dist"
echo "访问URL: https://douplus.easymai.cn/oauth/douplus.php"
echo ""

echo "4️⃣  测试OAuth授权URL生成"
echo "------------------------------------------"
echo "预期授权URL格式："
echo "https://open.oceanengine.com/audit/oauth.html?app_id=1854346912597002&state=douplus&material_auth=1"
echo ""

echo "5️⃣  完整流程说明"
echo "------------------------------------------"
echo "步骤1: 用户访问 https://douplus.easymai.cn/account/dashboard"
echo "步骤2: 点击'添加账号'按钮"
echo "步骤3: 系统调用 /api/account/oauth/url 生成授权链接"
echo "步骤4: 跳转到巨量引擎授权页面"
echo "步骤5: 授权成功后回调 https://douplus.easymai.cn/oauth/douplus.php"
echo "步骤6: PHP处理回调，保存账号信息"
echo "步骤7: 自动跳转回 https://douplus.easymai.cn/account/dashboard"
echo ""

echo "=========================================="
echo "✅ 配置验证完成"
echo "=========================================="
