#!/bin/bash
# 续费功能问题诊断脚本

echo "=========================================="
echo "续费功能完整诊断"
echo "=========================================="
echo ""

echo "📋 1. 检查前端源码中的图标导入"
echo "------------------------------------------"
echo "✅ RenewDialog.vue:"
grep -n "import.*VideoCamera.*from" /opt/douplus/douplus-web/src/components/order/RenewDialog.vue

echo ""
echo "✅ BatchRenewDialog.vue:"
grep -n "import.*VideoCamera.*from" /opt/douplus/douplus-web/src/components/order/BatchRenewDialog.vue

echo ""
echo "✅ account/Index.vue:"
grep -n "import.*QuestionFilled.*from" /opt/douplus/douplus-web/src/views/account/Index.vue

echo ""
echo ""

echo "📦 2. 检查前端构建状态"
echo "------------------------------------------"
if [ -f "/opt/douplus/douplus-web/dist/index.html" ]; then
    BUILD_TIME=$(stat -c%y /opt/douplus/douplus-web/dist/index.html | cut -d'.' -f1)
    echo "✅ 前端已构建: $BUILD_TIME"
    
    # 检查构建产物文件数量
    JS_COUNT=$(ls /opt/douplus/douplus-web/dist/assets/*.js 2>/dev/null | wc -l)
    CSS_COUNT=$(ls /opt/douplus/douplus-web/dist/assets/*.css 2>/dev/null | wc -l)
    echo "   JS文件: $JS_COUNT 个"
    echo "   CSS文件: $CSS_COUNT 个"
else
    echo "❌ 前端未构建"
fi

echo ""
echo ""

echo "🔧 3. 检查后端API字段名"
echo "------------------------------------------"
echo "✅ 所有 invest_password 引用："
grep -n "invest_password" /opt/douplus/douplus-sync-python/app/api/order_api.py | grep -v "invest_password_encrypted"

echo ""
echo "✅ 所有 access_token 引用："
grep -n "a\.access_token" /opt/douplus/douplus-sync-python/app/api/order_api.py

echo ""
echo ""

echo "🚀 4. 检查后端服务状态"
echo "------------------------------------------"
FLASK_PID=$(ps aux | grep "python3 api_server.py" | grep -v grep | awk '{print $2}')

if [ -n "$FLASK_PID" ]; then
    echo "✅ Flask运行中 (PID: $FLASK_PID)"
    
    # 检查端口监听
    PORT_INFO=$(lsof -i :5000 2>/dev/null | grep LISTEN)
    if [ -n "$PORT_INFO" ]; then
        echo "✅ 端口5000监听正常"
    else
        echo "❌ 端口5000未监听"
    fi
    
    # 检查最近日志
    echo ""
    echo "最近的API请求（最后10行）："
    tail -10 /opt/douplus/douplus-sync-python/logs/flask.log 2>/dev/null | grep -E "POST|GET|ERROR|WARNING" || echo "   (无日志或无最近请求)"
else
    echo "❌ Flask服务未运行"
fi

echo ""
echo ""

echo "🔍 5. 测试批量续费API（模拟调用）"
echo "------------------------------------------"
echo "尝试调用批量续费API（不带认证，仅测试路由）："
RESULT=$(curl -s -X POST http://localhost:5000/api/douplus/batch-renew \
  -H "Content-Type: application/json" \
  -d '{}' 2>&1)

if echo "$RESULT" | grep -q "401\|Unauthorized\|Missing token"; then
    echo "✅ API路由正常（返回401认证错误是预期的）"
elif echo "$RESULT" | grep -q "404\|Not Found"; then
    echo "❌ API路由404错误"
    echo "   返回: $RESULT"
else
    echo "API响应: $(echo $RESULT | head -c 200)"
fi

echo ""
echo ""

echo "🔍 6. 测试单次续费API（模拟调用）"
echo "------------------------------------------"
echo "尝试调用单次续费API（不带认证，仅测试路由）："
RESULT=$(curl -s -X POST http://localhost:5000/api/douplus/task/renew \
  -H "Content-Type: application/json" \
  -d '{}' 2>&1)

if echo "$RESULT" | grep -q "401\|Unauthorized\|Missing token"; then
    echo "✅ API路由正常（返回401认证错误是预期的）"
elif echo "$RESULT" | grep -q "404\|Not Found"; then
    echo "❌ API路由404错误"
    echo "   返回: $RESULT"
else
    echo "API响应: $(echo $RESULT | head -c 200)"
fi

echo ""
echo ""

echo "=========================================="
echo "💡 诊断建议"
echo "=========================================="
echo ""
echo "关于 'V is not a function' 错误："
echo "1. 这是Vue编译后的代码错误，通常是组件未正确导入"
echo "2. 请在浏览器控制台（F12 → Console）查看完整错误堆栈"
echo "3. 错误堆栈会显示具体是哪个文件、哪一行出错"
echo "4. 请提供错误堆栈的截图或文本"
echo ""
echo "关于批量续费0个订单："
echo "1. 后端API已修复字段名错误"
echo "2. 如果仍然失败，请查看后端日志："
echo "   tail -f /opt/douplus/douplus-sync-python/logs/flask.log"
echo "3. 在前端执行续费操作时观察日志中的错误"
echo ""
echo "建议操作："
echo "1. 打开浏览器开发者工具（F12）"
echo "2. 切换到 Console 标签"
echo "3. 点击续费按钮"
echo "4. 截图完整的错误堆栈信息"
echo "5. 同时查看 Network 标签中的API请求和响应"
echo ""
echo "=========================================="
