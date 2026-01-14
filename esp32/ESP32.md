# ESP32 LED 顏色夸張解釋方案

## 問題

Server 端使用 Plutchik 8 情緒模型，廣播 24 種顏色（8 情緒 × 3 強度），但 LED 實際顯示時：
- 青 (#00FFFF)、藍 (#0000FF)、深藍 (#000080) 看起來都像藍色
- 學生難以從 LED 顏色觀察「情緒流動」

## 解決方案

**Server 保持學術正確，ESP32 端做顏色重映射（夸張解釋）**

```
Server (8情緒) → MQTT → ESP32 (重映射) → LED (更易區分)
```

## 當前架構

### MQTT Topics
- `river/wheel/color` → `{"hex": "#FFFF00", "rgb": [255, 255, 0]}`
- `river/wheel/led_position` → `{"row": 0, "col": 1}`
- `river/wheel/result` → 完整結果

### ESP32 接收後
- `ledState.r/g/b` = RGB 值
- `ledState.position` = row * 10 + col（例：row=2, col=1 → position=21）

## 實現方案

### 方案 A：顏色重映射

在 `updateBreathing()` 中加入映射邏輯：

```cpp
void mapEmotionColor() {
    int row = ledState.position / 10;
    int col = ledState.position % 10;

    // 根據情緒類別重映射顏色（更容易區分）
    switch(row) {
        case 0: // 喜悅系 → 黃
            breathState.currentR = 255;
            breathState.currentG = 255;
            breathState.currentB = 0;
            break;
        case 1: // 信任系 → 綠
            breathState.currentR = 0;
            breathState.currentG = 255;
            breathState.currentB = 0;
            break;
        case 2: // 恐懼系 → 白（原本是青，太像藍）
            breathState.currentR = 200;
            breathState.currentG = 200;
            breathState.currentB = 255;
            break;
        case 3: // 驚喜系 → 青
            breathState.currentR = 0;
            breathState.currentG = 255;
            breathState.currentB = 255;
            break;
        case 4: // 悲傷系 → 藍
            breathState.currentR = 0;
            breathState.currentG = 0;
            breathState.currentB = 255;
            break;
        case 5: // 厭惡系 → 紫
            breathState.currentR = 255;
            breathState.currentG = 0;
            breathState.currentB = 255;
            break;
        case 6: // 憤怒系 → 紅
            breathState.currentR = 255;
            breathState.currentG = 0;
            breathState.currentB = 0;
            break;
        case 7: // 期待系 → 橙
            breathState.currentR = 255;
            breathState.currentG = 128;
            breathState.currentB = 0;
            break;
    }

    // 根據強度調整亮度 (col: 0=低, 1=中, 2=高)
    float intensityFactor = 0.4 + (col * 0.3); // 0.4, 0.7, 1.0
    breathState.currentR *= intensityFactor;
    breathState.currentG *= intensityFactor;
    breathState.currentB *= intensityFactor;
}
```

### 方案 B：動態效果區分

用不同的呼吸/閃爍模式區分情緒：

```cpp
struct EmotionEffect {
    int breathSpeed;      // 呼吸速度 (ms)
    bool enableFlash;     // 是否閃爍
    int flashInterval;    // 閃爍間隔
};

EmotionEffect emotionEffects[8] = {
    {3, false, 0},     // 喜悅：慢呼吸
    {3, false, 0},     // 信任：慢呼吸
    {2, true, 100},    // 恐懼：快閃爍
    {1, true, 200},    // 驚喜：中速閃爍
    {5, false, 0},     // 悲傷：很慢呼吸
    {2, false, 0},     // 厭惡：快呼吸
    {1, true, 50},     // 憤怒：急促閃爍
    {2, false, 0},     // 期待：快呼吸
};

void applyEmotionEffect() {
    int row = ledState.position / 10;
    EmotionEffect effect = emotionEffects[row];

    breathState.updateInterval = effect.breathSpeed;

    if (effect.enableFlash) {
        // 實現閃爍效果
    }
}
```

### 方案 C：混合（推薦）

顏色重映射 + 動態效果：

| 情緒 | 顏色 | 效果 |
|-----|------|------|
| 喜悅 | 黃 | 慢呼吸 |
| 信任 | 綠 | 慢呼吸 |
| 恐懼 | 淡藍白 | 快閃爍 |
| 驚喜 | 青 | 跳動 |
| 悲傷 | 深藍 | 很慢呼吸 |
| 厭惡 | 紫 | 快呼吸 |
| 憤怒 | 紅 | 急促閃爍 |
| 期待 | 橙 | 中速呼吸 |

## 待討論

1. 最終要用幾種情緒？（4 / 6 / 8）
2. 強度 (col) 要用亮度還是效果區分？
3. 是否需要「流動過渡動畫」？（從一個顏色漸變到另一個）

## 相關文件

- Server 情緒定義：`server/emotion_wheel.py`
- ESP32 當前代碼：`esp32/sketch_dec5a/sketch_dec5a.ino`
- MQTT Topics：`INTEGRATION.md`
