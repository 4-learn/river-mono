# River Server 測試腳本

這個資料夾包含了用於測試 River Server 的各種腳本。

## 📋 腳本列表

### 1. `test_wheel.sh` - API 端點測試

測試 `/wheel` 端點的功能，發送多個情緒測試案例。

**用法：**
```bash
./scripts/test_wheel.sh
```

**功能：**
- 測試 `/health` 健康檢查
- 測試 5 種不同的情緒輸入
- 顯示 API 回應的 JSON 結果

**前提條件：**
- River Server 正在運行（`http://localhost:9005`）
- 已安裝 `jq`（用於格式化 JSON）

---

### 2. `mqtt_subscribe.sh` - MQTT 訂閱（基本版）

訂閱所有 River 發布的 MQTT 訊息。

**用法：**
```bash
# 使用預設設定（test.mosquitto.org）
./scripts/mqtt_subscribe.sh

# 使用自訂 broker
MQTT_HOST=broker.hivemq.com ./scripts/mqtt_subscribe.sh

# 訂閱特定 topic
MQTT_TOPIC="river/wheel/led_position" ./scripts/mqtt_subscribe.sh
```

**顯示格式：**
```
[14:30:45] river/wheel/led_position -> {"row": 0, "col": 1}
[14:30:45] river/wheel/color -> {"hex": "#FFFF99", "rgb": [255, 255, 153]}
```

**環境變數：**
- `MQTT_HOST` - MQTT Broker 主機（預設：`test.mosquitto.org`）
- `MQTT_PORT` - MQTT Broker 端口（預設：`1883`）
- `MQTT_TOPIC` - 訂閱的 topic（預設：`river/wheel/#`）

**前提條件：**
- 已安裝 `mosquitto-clients`
  ```bash
  sudo apt install mosquitto-clients
  ```

---

### 3. `mqtt_subscribe_pretty.sh` - MQTT 訂閱（美化版）⭐

訂閱 River 的 MQTT 訊息，並以彩色、美化的方式顯示。

**用法：**
```bash
./scripts/mqtt_subscribe_pretty.sh
```

**顯示範例：**
```
=========================================
River MQTT 訂閱測試 (美化版)
=========================================

Broker: test.mosquitto.org:1883
Topic:  river/wheel/#

開始監聽... (按 Ctrl+C 停止)
=========================================

[14:30:45] 📍 LED Position
{
  "row": 0,
  "col": 1
}

[14:30:45] 🎨 Color
{
  "hex": "#FFFF99",
  "rgb": [255, 255, 153]
}

[14:30:45] 😊 Sentiment
{
  "name": "喜悅",
  "category": "joy"
}
```

**特色：**
- ✅ 彩色輸出（不同 topic 使用不同顏色）
- ✅ Emoji 圖示（LED 位置 📍、顏色 🎨、情緒 😊）
- ✅ JSON 自動美化（如果有安裝 `jq`）
- ✅ 時間戳記

**前提條件：**
- 已安裝 `mosquitto-clients`
- **建議**安裝 `jq` 以獲得最佳體驗
  ```bash
  sudo apt install jq
  ```

---

## 🧪 測試流程

### 完整測試 River Server

1. **啟動 River Server**
   ```bash
   cd /home/yillkid/workspace/4-learn/river-mono/server
   ./run.sh
   ```

2. **開啟新終端，訂閱 MQTT**
   ```bash
   cd /home/yillkid/workspace/4-learn/river-mono
   ./scripts/mqtt_subscribe_pretty.sh
   ```

3. **開啟第三個終端，測試 API**
   ```bash
   cd /home/yillkid/workspace/4-learn/river-mono
   ./scripts/test_wheel.sh
   ```

4. **觀察結果**
   - 終端 1：查看 Server 日誌
   - 終端 2：看到 MQTT 訊息即時發布
   - 終端 3：看到 API 回應

---

## 📡 MQTT Topics 說明

River Server 會發布到以下 topics：

| Topic | 內容 | Retain | 說明 |
|-------|------|--------|------|
| `river/wheel/led_position` | `{"row": int, "col": int}` | ✅ | LED 矩陣位置 |
| `river/wheel/color` | `{"hex": str, "rgb": [r,g,b]}` | ✅ | 情緒顏色 |
| `river/wheel/sentiment` | `{"name": str, "category": str}` | ✅ | 情緒標籤 |
| `river/wheel/result` | `{完整結果}` | ❌ | 完整資訊 |

### Retain 說明
- ✅ **Retain=True**: 訊息會保留在 broker，新訂閱者會立即收到最新值
- ❌ **Retain=False**: 訊息不保留，只有當時在線的訂閱者能收到

---

## 🔧 故障排除

### mosquitto_sub 未安裝
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mosquitto-clients

# CentOS/RHEL
sudo yum install mosquitto

# macOS
brew install mosquitto
```

### jq 未安裝（可選，但建議安裝）
```bash
# Ubuntu/Debian
sudo apt install jq

# CentOS/RHEL
sudo yum install jq

# macOS
brew install jq
```

### 連接 MQTT Broker 失敗
- 檢查網路連線
- 嘗試其他公開 broker：
  ```bash
  MQTT_HOST=broker.hivemq.com ./scripts/mqtt_subscribe.sh
  ```

### API 測試失敗
- 確認 River Server 正在運行
- 檢查端口是否正確（預設 9005）
- 查看 Server 日誌找出錯誤

---

## 📝 自訂測試

### 手動發送 API 請求
```bash
curl -X POST http://localhost:9005/wheel \
  -H "Content-Type: application/json" \
  -d '{"text": "你的文字", "position": [0, 0]}' | jq .
```

### 訂閱特定 topic
```bash
# 只訂閱 LED 位置
mosquitto_sub -h test.mosquitto.org -t "river/wheel/led_position" -v

# 只訂閱顏色
mosquitto_sub -h test.mosquitto.org -t "river/wheel/color" -v

# 只訂閱情緒
mosquitto_sub -h test.mosquitto.org -t "river/wheel/sentiment" -v
```

### 發布測試訊息
```bash
# 手動發布訊息到 MQTT
mosquitto_pub -h test.mosquitto.org \
  -t "river/wheel/test" \
  -m '{"test": "hello"}'
```

---

## 🎯 進階用法

### 記錄 MQTT 訊息到檔案
```bash
./scripts/mqtt_subscribe.sh > mqtt_log.txt
```

### 過濾特定關鍵字
```bash
./scripts/mqtt_subscribe.sh | grep "喜悅"
```

### 統計訊息數量
```bash
./scripts/mqtt_subscribe.sh | wc -l
```

---

## 📚 相關文件

- [INTEGRATION.md](../INTEGRATION.md) - River Server 整合說明
- [server/README.md](../server/README.md) - Server 配置說明

---

## ⚡ 快速測試指令

```bash
# 一鍵測試（需要三個終端）

# 終端 1: 啟動 Server
cd server && ./run.sh

# 終端 2: 監聽 MQTT
./scripts/mqtt_subscribe_pretty.sh

# 終端 3: 測試 API
./scripts/test_wheel.sh
```
