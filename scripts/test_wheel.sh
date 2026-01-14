#!/bin/bash

# 測試 /wheel 端點的腳本
# 使用方法: ./test_wheel.sh

# 設定伺服器 URL
SERVER_URL="http://localhost:9005"

echo "========================================="
echo "測試 River Mono - Wheel API"
echo "========================================="
echo ""

# 測試 1: Health Check
echo "測試 1: Health Check"
echo "-------------------"
curl -s "${SERVER_URL}/health" | jq .
echo ""
echo ""

# 測試 2: 喜悅情緒 (從平靜位置開始)
echo "測試 2: 表達喜悅情緒"
echo "-------------------"
echo "輸入文字: 今天天氣真好，我很開心！"
echo "當前位置: [0, 0] (平靜)"
echo ""
curl -s -X POST "${SERVER_URL}/wheel" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天氣真好，我很開心！",
    "position": [0, 0]
  }' | jq .
echo ""
echo ""

# 測試 3: 悲傷情緒
echo "測試 3: 表達悲傷情緒"
echo "-------------------"
echo "輸入文字: 我今天心情很低落，覺得很難過"
echo "當前位置: [0, 1] (喜悅)"
echo ""
curl -s -X POST "${SERVER_URL}/wheel" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我今天心情很低落，覺得很難過",
    "position": [0, 1]
  }' | jq .
echo ""
echo ""

# 測試 4: 憤怒情緒
echo "測試 4: 表達憤怒情緒"
echo "-------------------"
echo "輸入文字: 這件事真的讓我很生氣！"
echo "當前位置: [4, 1] (難過)"
echo ""
curl -s -X POST "${SERVER_URL}/wheel" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "這件事真的讓我很生氣！",
    "position": [4, 1]
  }' | jq .
echo ""
echo ""

# 測試 5: 驚喜情緒
echo "測試 5: 表達驚喜情緒"
echo "-------------------"
echo "輸入文字: 哇！這真是太令人驚訝了！"
echo "當前位置: [7, 1] (期待)"
echo ""
curl -s -X POST "${SERVER_URL}/wheel" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哇！這真是太令人驚訝了！",
    "position": [7, 1]
  }' | jq .
echo ""
echo ""

echo "========================================="
echo "測試完成"
echo "========================================="
