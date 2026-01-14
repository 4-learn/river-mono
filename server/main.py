import os
import base64
import time
import uuid
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

logger = logging.getLogger("uvicorn")

from emotion_wheel import get_emotion
from llm_service import analyze_emotion_and_respond
from mqtt_client import mqtt_client
from asr_service import yating_asr_from_wav16k, asr_fallback_openai
from tts_service import yating_tts_rest
from audio_utils import ffmpeg_to_wav16k_mono

load_dotenv()

app = FastAPI(title="River Server - Unified Emotion Analysis Engine")

# 全域情緒狀態記憶（簡單實作，生產環境建議用資料庫）
emotion_state = {
    "row": 0,
    "col": 1  # 預設從「喜悅」開始
}

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class WheelRequest(BaseModel):
    text: str
    position: List[int]

class LEDPosition(BaseModel):
    row: int
    col: int

class WheelResponse(BaseModel):
    led_position: LEDPosition
    color: str
    sentiment: str
    text: str

# ==================== Global State ====================

# TTS 背景任務佇列
TTS_JOBS: Dict[str, Dict[str, Any]] = {}

# ==================== Helper Functions ====================

def hex_to_rgb(hex_color: str) -> List[int]:
    """將 hex 顏色轉換為 RGB 陣列"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

def publish_emotion_result(led_position: dict, color: str, sentiment: str, category: str):
    """發布情緒結果到 MQTT"""
    try:
        rgb = hex_to_rgb(color)

        # 發布各個 topic
        mqtt_client.publish("led_position", led_position, qos=1, retain=True)
        mqtt_client.publish("color", {"hex": color, "rgb": rgb}, qos=1, retain=True)
        mqtt_client.publish("sentiment", {"name": sentiment, "category": category}, qos=1, retain=True)

        # 完整結果（不保留）
        mqtt_client.publish("result", {
            "led_position": led_position,
            "color": color,
            "sentiment": sentiment,
            "rgb": rgb
        }, qos=1, retain=False)

    except Exception as e:
        print(f"[MQTT] Publish error: {e}")

def _bg_make_tts(job_id: str, text: str, voice: str = "tai_female_1"):
    """背景任務：生成 TTS"""
    try:
        audio = yating_tts_rest(text, voice) or b""
        TTS_JOBS[job_id] = {
            "ready": True,
            "audio": base64.b64encode(audio).decode() if audio else ""
        }
    except Exception as e:
        TTS_JOBS[job_id] = {"ready": True, "audio": "", "error": str(e)}

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
def on_startup():
    """應用啟動時初始化 MQTT"""
    print("[River] Starting River Server...")
    mqtt_client.connect()
    print("[River] Server ready")

@app.on_event("shutdown")
def on_shutdown():
    """應用關閉時斷開 MQTT"""
    mqtt_client.disconnect()

# ==================== API Endpoints ====================

@app.get("/health")
async def health_check():
    """健康檢查（與 /healthz 相容）"""
    return {"status": "ok"}

@app.get("/emotion/state")
async def get_emotion_state():
    """取得當前情緒狀態"""
    current_emotion = get_emotion(emotion_state["row"], emotion_state["col"])
    return {
        "row": emotion_state["row"],
        "col": emotion_state["col"],
        "emotion": current_emotion
    }

@app.post("/emotion/reset")
async def reset_emotion_state(row: int = 0, col: int = 1):
    """重置情緒狀態到指定位置（預設為喜悅）"""
    if not (0 <= row < 8 and 0 <= col < 3):
        return JSONResponse({"error": "Invalid position"}, status_code=400)

    emotion_state["row"] = row
    emotion_state["col"] = col
    current_emotion = get_emotion(row, col)

    logger.info(f"[Main] 情緒狀態重置: ({row},{col}) - {current_emotion['name']}")

    return {
        "message": "Emotion state reset",
        "row": row,
        "col": col,
        "emotion": current_emotion
    }

@app.get("/healthz")
async def healthz():
    """健康檢查（Android APP 相容）"""
    return {"ok": True, "service": "river"}

@app.post("/wheel", response_model=WheelResponse)
async def wheel_endpoint(request: WheelRequest):
    """
    文字輸入的情緒分析端點（for Blockly）

    輸入：
        - text: 使用者輸入的文字
        - position: 當前位置 [row, col]

    輸出：
        - led_position: 新的 LED 位置
        - color: 情緒顏色 (hex)
        - sentiment: 情緒名稱
        - text: AI 回應文字
    """
    print("=" * 50)
    print("收到 /wheel 請求:")
    print(f"  text: {request.text}")
    print(f"  position: {request.position}")
    print("=" * 50)

    current_row = request.position[0]
    current_col = request.position[1]

    # 使用 LLM 分析情感並生成回應
    llm_result = analyze_emotion_and_respond(request.text, current_row, current_col)

    new_row = llm_result["target_row"]
    new_col = llm_result["target_col"]

    # 取得新位置的情感資訊
    emotion_info = get_emotion(new_row, new_col)

    print(f"  LLM 分析結果: {llm_result['detected_emotion']}")
    print(f"  新位置: ({new_row}, {new_col}) - {emotion_info['name']}")
    print(f"  顏色: {emotion_info['color']}")
    print("=" * 50)

    result = {
        "led_position": {"row": new_row, "col": new_col},
        "color": emotion_info["color"],
        "sentiment": emotion_info["name"],
        "text": llm_result["response_text"]
    }

    # 發布到 MQTT
    publish_emotion_result(
        result["led_position"],
        result["color"],
        result["sentiment"],
        emotion_info["category"]
    )

    return result

@app.post("/dialogue")
async def dialogue(file: UploadFile = File(...)):
    """
    完整模式：音檔輸入 → ASR → 情緒分析 → TTS → 完整結果
    (for Android APP - 完整模式)

    輸入：
        - file: 音檔 (任何格式)

    輸出：
        - text: 辨識出的文字
        - response: AI 回應文字
        - emotion: 情緒名稱
        - rgb: RGB 顏色陣列
        - led_position: LED 位置
        - sentiment: 情緒名稱
        - audio_wav_base64: TTS 音檔 (base64)
        - timings: 各階段耗時
    """
    try:
        raw_audio = await file.read()
        t_all = time.time()

        # (1) 轉換音檔為 16kHz mono WAV
        t0 = time.time()
        wav16k = ffmpeg_to_wav16k_mono(raw_audio)
        t1 = time.time()

        # (2) ASR 語音辨識 - 優先使用 Yating
        text = yating_asr_from_wav16k(wav16k) or ""
        if not text:
            print("[ASR] Yating failed, trying OpenAI fallback...")
            text = asr_fallback_openai(wav16k) or ""
        t2 = time.time()

        if not text:
            return JSONResponse({"error": "no_speech"}, status_code=400)

        logger.info(f"[ASR] 最終辨識結果: '{text}'")

        # (3) 情緒分析（使用上一次的情緒狀態）
        current_row, current_col = emotion_state["row"], emotion_state["col"]
        logger.info(f"[Main] 從上次位置開始: ({current_row},{current_col})")

        llm_result = analyze_emotion_and_respond(text, current_row, current_col)
        new_row = llm_result["target_row"]
        new_col = llm_result["target_col"]

        # 更新全域狀態
        emotion_state["row"] = new_row
        emotion_state["col"] = new_col
        logger.info(f"[Main] 情緒狀態更新: ({new_row},{new_col})")

        emotion_info = get_emotion(new_row, new_col)
        t3 = time.time()

        # (4) TTS 語音合成
        tts_bytes = yating_tts_rest(llm_result["response_text"]) or b""
        t4 = time.time()

        # 準備回應
        result = {
            "text": text,
            "response": llm_result["response_text"],
            "emotion": emotion_info["name"],
            "rgb": hex_to_rgb(emotion_info["color"]),
            "led_position": {"row": new_row, "col": new_col},
            "sentiment": emotion_info["name"],
            "audio_wav_base64": base64.b64encode(tts_bytes).decode() if tts_bytes else "",
            "timings": {
                "convert": round(t1 - t0, 3),
                "asr": round(t2 - t1, 3),
                "llm": round(t3 - t2, 3),
                "tts": round(t4 - t3, 3),
                "total_server": round(t4 - t_all, 3)
            }
        }

        # 發布到 MQTT
        publish_emotion_result(
            result["led_position"],
            emotion_info["color"],
            result["sentiment"],
            emotion_info["category"]
        )

        print(f"[/dialogue] Timings: {result['timings']}")
        return result

    except Exception as e:
        print(f"[/dialogue] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/dialogue_fast")
async def dialogue_fast(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    快速模式：音檔輸入 → ASR → 情緒分析 → 立即回傳（TTS 背景處理）
    (for Android APP - 快速模式)

    輸入：
        - file: 音檔 (任何格式)

    輸出：
        - text: 辨識出的文字
        - response: AI 回應文字
        - emotion: 情緒名稱
        - rgb: RGB 顏色陣列
        - led_position: LED 位置
        - sentiment: 情緒名稱
        - job_id: TTS 任務 ID（用於輪詢音檔）
        - timings: 各階段耗時（不含 TTS）
    """
    try:
        raw_audio = await file.read()
        t_all = time.time()

        # (1) 轉換音檔
        t0 = time.time()
        wav16k = ffmpeg_to_wav16k_mono(raw_audio)
        t1 = time.time()

        # (2) ASR 語音辨識 - 優先使用 Yating
        text = yating_asr_from_wav16k(wav16k) or ""
        if not text:
            print("[ASR] Yating failed, trying OpenAI fallback...")
            text = asr_fallback_openai(wav16k) or ""
        t2 = time.time()

        if not text:
            return JSONResponse({"error": "no_speech"}, status_code=400)

        # (3) 情緒分析（使用上一次的情緒狀態）
        current_row, current_col = emotion_state["row"], emotion_state["col"]
        logger.info(f"[Main] 從上次位置開始: ({current_row},{current_col})")

        llm_result = analyze_emotion_and_respond(text, current_row, current_col)
        new_row = llm_result["target_row"]
        new_col = llm_result["target_col"]

        # 更新全域狀態
        emotion_state["row"] = new_row
        emotion_state["col"] = new_col
        logger.info(f"[Main] 情緒狀態更新: ({new_row},{new_col})")

        emotion_info = get_emotion(new_row, new_col)
        t3 = time.time()

        # (4) 啟動背景 TTS
        job_id = uuid.uuid4().hex[:10]
        TTS_JOBS[job_id] = {"ready": False, "audio": ""}
        background_tasks.add_task(_bg_make_tts, job_id, llm_result["response_text"], "tai_female_1")

        # 準備回應
        result = {
            "text": text,
            "response": llm_result["response_text"],
            "emotion": emotion_info["name"],
            "rgb": hex_to_rgb(emotion_info["color"]),
            "led_position": {"row": new_row, "col": new_col},
            "sentiment": emotion_info["name"],
            "job_id": job_id,
            "timings": {
                "convert": round(t1 - t0, 3),
                "asr": round(t2 - t1, 3),
                "llm": round(t3 - t2, 3),
                "total_server_no_tts": round(time.time() - t_all, 3)
            }
        }

        # 發布到 MQTT
        publish_emotion_result(
            result["led_position"],
            emotion_info["color"],
            result["sentiment"],
            emotion_info["category"]
        )

        print(f"[/dialogue_fast] Timings (no TTS): {result['timings']} | job_id={job_id}")
        return result

    except Exception as e:
        print(f"[/dialogue_fast] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/audio/{job_id}")
def get_audio(job_id: str):
    """
    輪詢取得背景生成的 TTS 音檔
    (for Android APP - 快速模式)

    輸入：
        - job_id: TTS 任務 ID

    輸出：
        - ready: 是否已完成
        - audio_wav_base64: TTS 音檔 (base64)，如果已完成
        - error: 錯誤訊息（如果有）
    """
    job = TTS_JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "not_found"}, status_code=404)

    if not job["ready"]:
        return {"ready": False}

    return {
        "ready": True,
        "audio_wav_base64": job.get("audio", ""),
        "error": job.get("error")
    }

# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)
