# River Server 整合說明

## 🎯 整合完成

River Server 現在是一個**統一的情緒分析引擎**，同時支援：
- **Blockly** (文字輸入)
- **Android APP** (語音輸入)
- **未來的所有 Client**

所有請求都使用相同的 **8×3 情緒網格**，並透過 **MQTT 發布**結果。

---

## 📋 新增功能

### 1. **MQTT 發布**
所有端點的情緒分析結果都會自動發布到 MQTT：

**Topics:**
```
river/wheel/led_position    -> {"row": 0, "col": 1}
river/wheel/color           -> {"hex": "#FFFF99", "rgb": [255, 255, 153]}
river/wheel/sentiment       -> {"name": "喜悅", "category": "joy"}
river/wheel/result          -> {完整結果}
```

### 2. **語音處理端點**

#### `/dialogue` - 完整模式
- 輸入：音檔 (任何格式)
- 輸出：ASR 文字 + 情緒分析 + TTS 音檔 (base64)
- 用途：Android APP 完整模式

#### `/dialogue_fast` - 快速模式
- 輸入：音檔 (任何格式)
- 輸出：ASR 文字 + 情緒分析 + job_id
- TTS 在背景處理，透過 `/audio/{job_id}` 輪詢
- 用途：Android APP 快速模式

#### `/audio/{job_id}` - 音檔輪詢
- 輸入：job_id
- 輸出：TTS 音檔 (base64) 或 ready=false
- 用途：取得背景生成的 TTS

### 3. **兼容端點**

#### `/healthz` - 健康檢查
- 與 Android APP 的 `/healthz` 相容
- 同時保留 `/health` 端點

---

## 🏗️ 架構圖

```
┌─────────────────────────────────────────────────────────┐
│              River Server (Port 9005)                   │
│         Unified Emotion Analysis Engine                 │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐  ┌───▼─────┐  ┌──▼──────┐
│Blockly │  │Android  │  │ MQTT    │
│(文字)   │  │APP(語音) │  │Broker   │
└────────┘  └─────────┘  └─────────┘
    │            │            │
    │    ┌───────┴────────┐   │
    │    │                │   │
    ▼    ▼                ▼   ▼
┌────────────────────────────────┐
│   Emotion Wheel (8×3 Grid)     │
│   - 8 基本情緒類別              │
│   - 3 強度等級                  │
│   - LLM 智能分析                │
└────────────────────────────────┘
```

---

## 📦 新增模組

### 1. `mqtt_client.py`
MQTT 客戶端管理：
- 自動連接和重連
- 訊息佇列（連接失敗時暫存）
- 支援 TLS

### 2. `asr_service.py`
語音辨識服務：
- Yating ASR (主要)
- OpenAI Whisper (備援)
- 早停機制（減少延遲）

### 3. `tts_service.py`
語音合成服務：
- Yating TTS REST API
- 台語語音 (tai_female_1)

### 4. `audio_utils.py`
音檔處理工具：
- FFmpeg 格式轉換
- 16kHz mono WAV 輸出
- 尾端靜音移除

---

## 🔧 環境設定

### 1. 安裝依賴

```bash
cd /home/yillkid/workspace/4-learn/river-mono/server
pip install -r requirements.txt
```

### 2. 更新 .env

複製並編輯環境變數：
```bash
cp .env.example .env
nano .env
```

必要設定：
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Yating
YATING_API_KEY=your_key_here

# MQTT (已預設為 test.mosquitto.org)
MQTT_HOST=test.mosquitto.org
MQTT_PORT=1883
```

### 3. 安裝 FFmpeg

如果系統沒有 FFmpeg：
```bash
sudo apt update
sudo apt install ffmpeg -y
```

---

## 🚀 啟動服務

```bash
cd /home/yillkid/workspace/4-learn/river-mono/server
./run.sh
```

或手動啟動：
```bash
python main.py
```

服務會運行在：`http://0.0.0.0:9005`

---

## 📡 MQTT 訂閱測試

使用 `mosquitto_sub` 測試 MQTT 發布：

```bash
# 訂閱所有 river/wheel 的訊息
mosquitto_sub -h test.mosquitto.org -t "river/wheel/#" -v

# 只訂閱 LED 位置
mosquitto_sub -h test.mosquitto.org -t "river/wheel/led_position" -v

# 只訂閱顏色
mosquitto_sub -h test.mosquitto.org -t "river/wheel/color" -v
```

---

## 🧪 API 測試

### 測試 /wheel (Blockly 用)
```bash
curl -X POST http://localhost:9005/wheel \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天心情很好！",
    "position": [0, 0]
  }'
```

### 測試 /healthz (Android APP 用)
```bash
curl http://localhost:9005/healthz
```

### 測試 /dialogue (需要音檔)
```bash
curl -X POST http://localhost:9005/dialogue \
  -F "file=@test.webm"
```

---

## 📊 端點對照表

| 端點 | Client | 輸入 | 輸出 | MQTT 發布 |
|------|--------|------|------|-----------|
| `/wheel` | Blockly | 文字 + 位置 | 情緒分析 | ✅ |
| `/dialogue` | Android (完整) | 音檔 | ASR + 情緒 + TTS | ✅ |
| `/dialogue_fast` | Android (快速) | 音檔 | ASR + 情緒 + job_id | ✅ |
| `/audio/{job_id}` | Android | job_id | TTS 音檔 | ❌ |
| `/health` | 監控 | - | 健康狀態 | ❌ |
| `/healthz` | Android | - | 健康狀態 | ❌ |

---

## 🎨 MQTT 發布格式

### LED 位置
```json
Topic: river/wheel/led_position
Payload: {"row": 0, "col": 1}
QoS: 1, Retain: true
```

### 顏色
```json
Topic: river/wheel/color
Payload: {
  "hex": "#FFFF99",
  "rgb": [255, 255, 153]
}
QoS: 1, Retain: true
```

### 情緒標籤
```json
Topic: river/wheel/sentiment
Payload: {
  "name": "喜悅",
  "category": "joy"
}
QoS: 1, Retain: true
```

### 完整結果
```json
Topic: river/wheel/result
Payload: {
  "led_position": {"row": 0, "col": 1},
  "color": "#FFFF99",
  "sentiment": "喜悅",
  "rgb": [255, 255, 153]
}
QoS: 1, Retain: false
```

---

## 🔍 除錯

### 查看 MQTT 連接狀態
啟動服務後查看 log：
```
[MQTT] Initialized: test.mosquitto.org:1883 (TLS=False)
[MQTT] Connected to test.mosquitto.org:1883
```

### 查看 MQTT 發布
每次請求後會看到：
```
[MQTT] Published: river/wheel/led_position -> {"row":0,"col":1}
[MQTT] Published: river/wheel/color -> {"hex":"#FFFF99","rgb":[255,255,153]}
```

### 常見問題

**Q: MQTT 連接失敗？**
A: 檢查防火牆和網路，或使用其他 broker (如 `broker.hivemq.com`)

**Q: ASR 沒有結果？**
A: 檢查 YATING_API_KEY 是否正確，或查看 OpenAI fallback 是否生效

**Q: FFmpeg not found？**
A: 執行 `sudo apt install ffmpeg`

---

## 📝 下一步

1. ✅ 測試 `/wheel` 端點
2. ✅ 測試 MQTT 發布
3. ⏳ 使用 Android APP 測試 `/dialogue_fast`
4. ⏳ 訂閱 MQTT 驗證實時更新

---

## 🎉 完成！

River Server 現在是一個完整的統一情緒分析引擎，支援：
- ✅ 文字和語音輸入
- ✅ 8×3 情緒網格
- ✅ MQTT 實時發布
- ✅ Blockly 和 Android APP 兼容
- ✅ 可擴展給未來的 Client
