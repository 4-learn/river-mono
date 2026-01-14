# 🌳 TreeHole 樹洞客戶端

一個支援台語語音對話的 Android WebView 應用程式，具備情感辨識和動態介面變色功能。

## ✨ 功能特色

### 🎤 語音互動
- **按住說話**：直覺的錄音操作方式
- **台語支援**：專為台語語音辨識優化
- **即時回放**：錄音後立即播放確認
- **高品質 TTS**：雅婷台語語音合成

### 🎨 情感變色
- **即時情感分析**：AI 分析對話情感
- **動態介面變色**：根據情感改變整個 APP 色調
- **10 種情感色彩**：happy, sad, angry, anxious, calm, excited, confused, grateful, lonely, hopeful

### ⚡ 雙模式處理
- **快速模式**：ASR + LLM 先回應，TTS 背景生成
- **完整模式**：等待所有處理完成後一次回應

## 🏗️ 技術架構

### 前端 (Android WebView)
- **HTML5 + JavaScript**：現代化 Web 技術
- **MediaRecorder API**：原生音頻錄製
- **Audio API**：音檔播放控制
- **Fetch API**：與後端 RESTful 通訊

### 後端 API
- **FastAPI** Python 伺服器
- **雅婷 ASR**：台語語音辨識
- **OpenAI GPT-4o-mini**：對話生成
- **雅婷 TTS**：台語語音合成
- **FFmpeg**：音檔格式轉換

## 📱 使用說明

### 基本操作
1. **設定伺服器**：輸入後端 API 地址
2. **選擇模式**：快速模式或完整模式
3. **測試連接**：確認與伺服器連線正常
4. **按住說話**：按住錄音按鈕開始對話
5. **聆聽回應**：AI 回應會自動播放

### 介面說明
- **🎤 錄音按鈕**：按住說話，鬆開停止
- **📊 狀態顯示**：顯示當前處理狀態
- **🔧 除錯區域**：顯示詳細操作日誌
- **💬 對話記錄**：顯示您說的話和 AI 回應
- **🔊 播放按鈕**：重播 AI 語音回應

### 情感變色系統
APP 會根據對話內容自動變色：
- 🟡 **開心 (Happy)**：溫暖黃色調
- 🔵 **難過 (Sad)**：沉靜藍色調
- 🔴 **生氣 (Angry)**：激烈紅色調
- 🟠 **焦慮 (Anxious)**：警示橙色調
- 🟢 **平靜 (Calm)**：舒緩綠色調
- 🟣 **興奮 (Excited)**：活力紫色調

## 🔧 開發部署

### Android 端
```kotlin
// MainActivity.kt
class MainActivity : ComponentActivity() {
    // WebView 設定載入 assets/index.html
    // 支援麥克風權限請求
    // HTTPS 網域映射到本地 assets
}
```

### 伺服器端
```bash
# 安裝相依套件
pip install fastapi uvicorn openai ailabs_asr

# 設定環境變數
export OPENAI_API_KEY="your_openai_key"
export YATING_API_KEY="your_yating_key"

# 啟動伺服器
uvicorn app:app --host 0.0.0.0 --port 8000
```

### API 端點
- `GET /healthz` - 健康檢查
- `POST /dialogue` - 完整模式對話
- `POST /dialogue_fast` - 快速模式對話
- `GET /audio/{job_id}` - 取得 TTS 音檔

## ⚙️ 設定說明

### 環境變數
```env
# OpenAI 設定
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key
OPENAI_TIMEOUT=15

# 雅婷 API 設定
YATING_API_KEY=your_yating_api_key
YATING_TTS_ENDPOINT=https://tts.api.yating.tw
YATING_TTS_TIMEOUT=20

# ASR 調校參數
ASR_MAX_WAIT=12.0
ASR_FIRST_CB_WAIT=2.0
ASR_STABILITY_GAP=0.8
ASR_GRACE_TAIL=1.5
```

### Android 權限
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

## 🚀 效能優化

### 快速模式流程
1. **錄音** → 立即開始錄製
2. **上傳** → 音檔上傳到伺服器
3. **ASR + LLM** → 語音辨識 + 對話生成 (2-3秒)
4. **即時回應** → 先顯示文字回應
5. **背景 TTS** → 同時生成語音檔案
6. **輪詢音檔** → 完成後自動播放

### 記憶體管理
- 自動清理暫存音檔
- URL.revokeObjectURL 避免記憶體洩漏
- Debug 日誌限制行數避免過度佔用

## 🔍 故障排除

### 常見問題

**錄音無法使用**
- 檢查麥克風權限是否開啟
- 確認 Android 系統版本支援 MediaRecorder

**無法連接伺服器**
- 確認網路連線狀態
- 檢查伺服器地址是否正確
- 測試 HTTPS 憑證是否有效

**語音辨識不準確**
- 建議在安靜環境下使用
- 說話清楚，語速適中
- 確認使用台語而非國語

**播放沒有聲音**
- 檢查裝置音量設定
- 確認音檔是否正確下載
- 查看 Debug 日誌了解詳細錯誤

### Debug 模式
開啟除錯區域可查看：
- 錄音檔案大小和格式
- 伺服器回應狀態
- 音檔輪詢進度
- 錯誤訊息詳情

## 📄 授權條款

本專案採用 MIT 授權條款。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設定
1. Clone 專案
2. 設定 Android 開發環境
3. 配置後端 API 金鑰
4. 測試錄音和播放功能

### 程式碼風格
- JavaScript: ES6+ 語法
- Kotlin: Android 官方風格指南
- Python: PEP 8 規範

---

**TreeHole 樹洞** - 讓 AI 傾聽你的台語心聲 💙
