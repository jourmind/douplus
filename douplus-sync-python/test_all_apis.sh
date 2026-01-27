#!/bin/bash
# 测试所有API接口

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSIsImV4cCI6MTc2OTg1MTU4N30.8fIW6DWJa5Hk0YuvHRm9m6N-qVAaNvElhp3VqBh8Uyc"
BASE_URL="https://42.194.181.242"

echo "========================================="
echo "测试所有API接口"
echo "========================================="
echo

# 1. 账号管理相关API
echo "【账号管理】"
echo "1. GET /api/account/list"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/account/list" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

echo "2. GET /api/account/page?pageNum=1&pageSize=10"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/account/page?pageNum=1&pageSize=10" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

echo "3. GET /api/account/oauth/url"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/account/oauth/url" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

# 2. DOU+相关API
echo "【DOU+投放记录】"
echo "4. GET /api/douplus/task/page?pageNum=1&pageSize=10"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/douplus/task/page?pageNum=1&pageSize=10" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

echo "5. GET /api/douplus/sync/status"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/douplus/sync/status" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

# 3. 统计相关API
echo "【统计数据】"
echo "6. GET /api/douplus/stats/dashboard"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/douplus/stats/dashboard" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

echo "7. GET /api/douplus/video/rankings?pageNum=1&pageSize=10"
curl -s -w "\n状态码: %{http_code}\n" "$BASE_URL/api/douplus/video/rankings?pageNum=1&pageSize=10" -H "Authorization: Bearer $TOKEN" -k | head -5
echo

echo "========================================="
echo "测试完成"
echo "========================================="
