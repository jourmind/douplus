#!/bin/bash
# 测试账号列表API

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSIsImV4cCI6MTc2OTg1MTU4N30.8fIW6DWJa5Hk0YuvHRm9m6N-qVAaNvElhp3VqBh8Uyc"

echo "========================================"
echo "测试账号列表API"
echo "========================================"
echo

echo "1. 测试 /api/account/list"
curl -s "https://127.0.0.1/api/account/list" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq '.'

echo
echo "========================================"
echo "2. 测试 /api/douplus/account/list"
curl -s "https://127.0.0.1/api/douplus/account/list" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq '.'

echo
echo "========================================"
echo "3. 直接测试后端5000端口"
curl -s "http://127.0.0.1:5000/api/account/list" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo
echo "========================================"
