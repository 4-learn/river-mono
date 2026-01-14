import os
import time
import json
import logging
import tempfile
from typing import Optional
from dotenv import load_dotenv
import requests
import websocket

load_dotenv()

logger = logging.getLogger("uvicorn")

ASR_MAX_WAIT = float(os.getenv("ASR_MAX_WAIT", "15.0"))
YATING_API_KEY = os.getenv("YATING_API_KEY", "").strip()

YATING_TOKEN_URL = "https://asr.api.yating.tw/v1/token"
YATING_WS_URL = "wss://asr.api.yating.tw/ws/v1/"


def yating_asr_from_wav16k(wav16k_bytes: bytes, pipeline: str = "asr-zh-tw-std", max_wait: float = ASR_MAX_WAIT) -> Optional[str]:
    """使用 Yating ASR (直接 WebSocket) 進行語音辨識"""
    logger.info(f"[ASR-Yating] 開始辨識，音檔: {len(wav16k_bytes)} bytes, pipeline: {pipeline}")
    
    if not YATING_API_KEY:
        logger.error("[ASR-Yating] YATING_API_KEY is empty")
        return None
    
    # (1) 取得 Token
    try:
        resp = requests.post(
            YATING_TOKEN_URL,
            json={"pipeline": pipeline},
            headers={"key": YATING_API_KEY},
            timeout=10
        )
        if resp.status_code != 201:
            logger.error(f"[ASR-Yating] Token API failed: {resp.status_code} {resp.text}")
            return None
        token = resp.json().get("auth_token", "")
        logger.info(f"[ASR-Yating] Got token: {token[:8]}...")
    except Exception as e:
        logger.error(f"[ASR-Yating] Token API error: {e}")
        return None
    
    # (2) 同步 WebSocket
    t0 = time.time()
    ws_url = f"{YATING_WS_URL}?token={token}"
    result = None
    
    try:
        ws = websocket.create_connection(ws_url, timeout=max_wait)
        logger.info("[ASR-Yating] WS connected")
        
        # 等待 session_started
        msg = ws.recv()
        data = json.loads(msg)
        logger.info(f"[ASR-Yating] recv: {data}")
        
        if data.get("message_type") != "session_started":
            logger.error(f"[ASR-Yating] Expected session_started, got: {data}")
            ws.close()
            return None
        
        # 發送 raw PCM（跳過 44 bytes WAV header）
        audio_data = wav16k_bytes[44:] if len(wav16k_bytes) > 44 else wav16k_bytes
        
        # 分塊發送 (每塊 3200 bytes = 100ms @ 16kHz mono 16bit)
        chunk_size = 3200
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            ws.send_binary(chunk)
            time.sleep(0.05)
        
        logger.info(f"[ASR-Yating] Sent {len(audio_data)} PCM bytes")
        
        # 發送空 binary 作為 EOF（跟 SDK 一樣）
        ws.send_binary(b'')
        logger.info("[ASR-Yating] Sent EOF (empty binary)")
        
        # 接收結果
        while (time.time() - t0) < max_wait:
            try:
                ws.settimeout(2.0)
                msg = ws.recv()
                data = json.loads(msg)
                logger.info(f"[ASR-Yating] recv: {data}")
                
                # 結果在 pipe.asr_sentence
                if 'pipe' in data:
                    pipe = data['pipe']
                    if 'asr_sentence' in pipe:
                        result = pipe['asr_sentence']
                        logger.info(f"[ASR-Yating] Got sentence: '{result}'")
                    
                    # 檢查是否最終結果
                    if pipe.get('asr_final'):
                        logger.info("[ASR-Yating] Got final")
                        break
                    
                    # 檢查 EOF
                    if pipe.get('asr_eof'):
                        logger.info("[ASR-Yating] Got EOF")
                        break
                        
            except websocket.WebSocketTimeoutException:
                if result:
                    logger.info("[ASR-Yating] Timeout but have result")
                    break
                continue
            except Exception as e:
                logger.warning(f"[ASR-Yating] Recv error: {e}")
                break
        
        ws.close()
        
    except Exception as e:
        logger.error(f"[ASR-Yating] WS error: {e}")
        return None
    
    took = time.time() - t0
    final_result = (result or "").strip() or None
    logger.info(f"[ASR-Yating] Took {took:.2f}s, result: '{final_result}'")
    return final_result


def asr_fallback_openai(wav16k_bytes: bytes) -> Optional[str]:
    """使用 OpenAI Whisper 作為備援 ASR"""
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.warning("[ASR-OpenAI] No API key")
            return None
        client = OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"[ASR-OpenAI] Init failed: {e}")
        return None
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav16k_bytes)
        f.flush()
        path = f.name
    
    try:
        try:
            with open(path, "rb") as fh:
                resp = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=fh)
            text = (resp.text or "").strip()
            if text:
                logger.info(f"[ASR-OpenAI] gpt-4o-transcribe: '{text}'")
                return text
        except Exception as e:
            logger.warning(f"[ASR-OpenAI] gpt-4o-transcribe failed: {e}")
        
        try:
            with open(path, "rb") as fh:
                resp = client.audio.transcriptions.create(model="whisper-1", file=fh)
            text = (resp.text or "").strip()
            if text:
                logger.info(f"[ASR-OpenAI] whisper-1: '{text}'")
                return text
        except Exception as e:
            logger.warning(f"[ASR-OpenAI] whisper-1 failed: {e}")
        
        return None
    finally:
        try:
            os.unlink(path)
        except:
            pass
