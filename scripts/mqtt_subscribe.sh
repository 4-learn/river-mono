#!/bin/bash

# MQTT 訂閱測試腳本
# 用於監聽 River Server 發布的情緒分析結果

# 設定 MQTT Broker
MQTT_HOST="${MQTT_HOST:-test.mosquitto.org}"
MQTT_PORT="${MQTT_PORT:-1883}"
MQTT_TOPIC="${MQTT_TOPIC:-river/wheel/#}"

echo "========================================="
echo "River MQTT 訂閱測試"
echo "========================================="
echo ""
echo "Broker: ${MQTT_HOST}:${MQTT_PORT}"
echo "Topic:  ${MQTT_TOPIC}"
echo ""
echo "開始監聽... (按 Ctrl+C 停止)"
echo "========================================="
echo ""

# 檢查是否安裝了 mosquitto_sub
if ! command -v mosquitto_sub &> /dev/null; then
    echo "❌ 錯誤: mosquitto_sub 未安裝"
    echo ""
    echo "請安裝 mosquitto-clients:"
    echo "  Ubuntu/Debian: sudo apt install mosquitto-clients"
    echo "  CentOS/RHEL:   sudo yum install mosquitto"
    echo "  macOS:         brew install mosquitto"
    exit 1
fi

# 使用 mosquitto_sub 訂閱
# -h: broker host
# -p: broker port
# -t: topic (# 表示訂閱所有子 topic)
# -v: verbose，顯示 topic 名稱
# -F: 格式化輸出

mosquitto_sub \
    -h "${MQTT_HOST}" \
    -p "${MQTT_PORT}" \
    -t "${MQTT_TOPIC}" \
    -v \
    -F "[%I:%M:%S] %t -> %p"
