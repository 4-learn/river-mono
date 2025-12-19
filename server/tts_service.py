import os
import time
import base64
import logging
import requests
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 檔案

logger = logging.getLogger("uvicorn")

YATING_API_KEY = os.getenv("YATING_API_KEY", "").strip()
YATING_TTS_ENDPOINT = os.getenv("YATING_TTS_ENDPOINT", "https://tts.api.yating.tw").strip()
YATING_TTS_TIMEOUT = float(os.getenv("YATING_TTS_TIMEOUT", "12"))


def normalize_yating_base(raw: str) -> str:
    """標準化 Yating TTS 端點 URL"""
    raw = (raw or "").strip()
    if not raw.startswith("http"):
        raw = "https://" + raw if raw else "https://tts.api.yating.tw"
    u = urlparse(raw)
    host = u.netloc or "tts.api.yating.tw"
    return f"https://{host}"


def yating_tts_rest(text: str, voice: str = "tai_female_1") -> Optional[bytes]:
    """
    使用 Yating TTS REST API 將文字轉為語音

    Args:
        text: 要合成的文字
        voice: 語音模型，預設為台語女聲

    Returns:
        WAV 音檔的 bytes，失敗則返回 None
    """
    key = YATING_API_KEY
    if not key:
        logger.error("[TTS] YATING_API_KEY is empty")
        return None

    base = normalize_yating_base(YATING_TTS_ENDPOINT)
    url = f"{base}/v2/speeches/short"
    headers = {"key": key, "Content-Type": "application/json"}
    payload = {
        "input": {"text": text, "type": "text"},
        "voice": {"model": voice, "speed": 1.1, "pitch": 1.0, "energy": 1.0},
        "audioConfig": {"encoding": "LINEAR16", "sampleRate": "16K"}
    }

    try:
        t0 = time.time()
        r = requests.post(url, headers=headers, json=payload, timeout=YATING_TTS_TIMEOUT)
        took = time.time() - t0

        if r.status_code == 401:
            logger.error(f"[TTS] 401 Unauthorized | took={took:.3f}s")
            return None

        r.raise_for_status()
        data = r.json()
        b64 = data.get("audioContent")

        if not b64:
            logger.error(f"[TTS] No audioContent in response | took={took:.3f}s")
            return None

        logger.info(f"[TTS] Success | took={took:.3f}s | b64_len={len(b64)}")
        return base64.b64decode(b64)

    except requests.exceptions.Timeout:
        logger.error(f"[TTS] Timeout after {YATING_TTS_TIMEOUT}s")
        return None
    except Exception as e:
        logger.error(f"[TTS] Error: {e}")
        return None
