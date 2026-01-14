#!/bin/bash

# MQTT 訂閱測試腳本 (美化版)
# 用於監聽 River Server 發布的情緒分析結果，並美化顯示 JSON

# 設定 MQTT Broker
MQTT_HOST="${MQTT_HOST:-test.mosquitto.org}"
MQTT_PORT="${MQTT_PORT:-1883}"
MQTT_TOPIC="${MQTT_TOPIC:-river/wheel/#}"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}River MQTT 訂閱測試 (美化版)${NC}"
echo -e "${CYAN}=========================================${NC}"
echo ""
echo -e "${YELLOW}Broker:${NC} ${MQTT_HOST}:${MQTT_PORT}"
echo -e "${YELLOW}Topic:${NC}  ${MQTT_TOPIC}"
echo ""
echo -e "${GREEN}開始監聽... (按 Ctrl+C 停止)${NC}"
echo -e "${CYAN}=========================================${NC}"
echo ""

# 檢查是否安裝了必要工具
if ! command -v mosquitto_sub &> /dev/null; then
    echo -e "${RED}❌ 錯誤: mosquitto_sub 未安裝${NC}"
    echo ""
    echo "請安裝 mosquitto-clients:"
    echo "  Ubuntu/Debian: sudo apt install mosquitto-clients"
    echo "  CentOS/RHEL:   sudo yum install mosquitto"
    echo "  macOS:         brew install mosquitto"
    exit 1
fi

# 檢查是否有 jq (用於美化 JSON)
HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

# 處理訂閱訊息
mosquitto_sub \
    -h "${MQTT_HOST}" \
    -p "${MQTT_PORT}" \
    -t "${MQTT_TOPIC}" \
    -v | while read -r line; do

    # 提取 topic 和 payload
    topic=$(echo "$line" | cut -d' ' -f1)
    payload=$(echo "$line" | cut -d' ' -f2-)

    # 取得時間戳
    timestamp=$(date +"%H:%M:%S")

    # 根據 topic 顯示不同顏色
    case "$topic" in
        *led_position*)
            echo -e "${BLUE}[${timestamp}]${NC} ${PURPLE}📍 LED Position${NC}"
            ;;
        *color*)
            echo -e "${BLUE}[${timestamp}]${NC} ${YELLOW}🎨 Color${NC}"
            ;;
        *sentiment*)
            echo -e "${BLUE}[${timestamp}]${NC} ${GREEN}😊 Sentiment${NC}"
            ;;
        *result*)
            echo -e "${BLUE}[${timestamp}]${NC} ${CYAN}📦 Full Result${NC}"
            ;;
        *)
            echo -e "${BLUE}[${timestamp}]${NC} ${topic}"
            ;;
    esac

    # 顯示 payload (如果有 jq 就美化)
    if [ "$HAS_JQ" = true ]; then
        echo "$payload" | jq --color-output '.' 2>/dev/null || echo "$payload"
    else
        echo "$payload"
    fi

    echo ""
done
