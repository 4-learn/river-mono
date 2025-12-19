import os
import time
import logging
import tempfile
import threading
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 檔案

logger = logging.getLogger("uvicorn")

# ASR 參數配置
ASR_MAX_WAIT = float(os.getenv("ASR_MAX_WAIT", "12.0"))
ASR_STABILITY_GAP = float(os.getenv("ASR_STABILITY_GAP", "0.5"))
FIRST_CB_WAIT = float(os.getenv("ASR_FIRST_CB_WAIT", "2.0"))
GRACE_TAIL = float(os.getenv("ASR_GRACE_TAIL", "0.8"))
YATING_API_KEY = os.getenv("YATING_API_KEY", "").strip()

def yating_asr_from_wav16k(wav16k_bytes: bytes, max_wait: float = ASR_MAX_WAIT) -> Optional[str]:
    """
    使用 Yating ASR SDK 進行語音辨識

    Args:
        wav16k_bytes: 16kHz mono WAV 音檔
        max_wait: 最長等待時間（秒）

    Returns:
        辨識出的文字，失敗則返回 None
    """
    logger.info(f"[ASR] 開始辨識，音檔大小: {len(wav16k_bytes)} bytes ({len(wav16k_bytes)/1024:.2f} KB)")

    if not YATING_API_KEY:
        logger.error("[ASR] YATING_API_KEY is empty")
        return None

    try:
        from ailabs_asr.streaming import StreamingClient
    except Exception as e:
        logger.error(f"[ASR] SDK not available: {e}")
        return None

    # 寫入臨時檔案
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav16k_bytes)
        f.flush()
        tmp_path = f.name

    state = {
        "result": None,
        "done": False,
        "last_update": time.time(),
        "error": None,
        "got_any_callback": False
    }
    first_cb = threading.Event()

    def on_processing_sentence(msg):
        text = (msg.get("asr_sentence") or "").strip()
        state["got_any_callback"] = True
        first_cb.set()
        if text and (not state["result"] or len(text) > len(state["result"])):
            state["result"] = text
        state["last_update"] = time.time()
        logger.info(f"[ASR] partial='{text}'")

    def on_final_sentence(msg):
        text = (msg.get("asr_sentence") or "").strip()
        state["got_any_callback"] = True
        first_cb.set()
        if text:
            state["result"] = text
        state["done"] = True
        state["last_update"] = time.time()
        logger.info(f"[ASR] final='{text}'")

    def worker():
        try:
            logger.info("[ASR] 建立 Yating StreamingClient...")
            cli = StreamingClient(key=YATING_API_KEY)
            logger.info(f"[ASR] 開始串流辨識，檔案: {tmp_path}")
            cli.start_streaming_wav(
                pipeline="asr-zh-tw-std",
                file=tmp_path,
                on_processing_sentence=on_processing_sentence,
                on_final_sentence=on_final_sentence
            )
            logger.info("[ASR] 串流辨識完成")
        except Exception as e:
            state["error"] = e
            logger.error(f"[ASR] Worker error: {e}", exc_info=True)
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    t0 = time.time()
    th = threading.Thread(target=worker, daemon=True)
    th.start()

    # 等待首次回呼
    first_cb.wait(timeout=FIRST_CB_WAIT)

    # 主迴圈：優先等待 done，只在超時時才早停
    while True:
        now = time.time()

        # 優先：等待 final callback
        if state["done"]:
            logger.info(f"[ASR] Final result after {now - t0:.2f}s")
            break

        # 只在接近超時時才考慮早停
        if (now - t0) > (max_wait * 0.8):  # 80% 超時時間後才檢查早停
            if state["result"] and (now - state["last_update"]) > ASR_STABILITY_GAP:
                logger.warning(f"[ASR] Early stop after {now - t0:.2f}s (approaching timeout, stable {ASR_STABILITY_GAP}s)")
                break

        # 絕對超時
        if (now - t0) > max_wait:
            logger.warning(f"[ASR] Timeout after {max_wait}s, grace period {GRACE_TAIL}s")
            end = now + GRACE_TAIL
            while time.time() < end:
                if state["done"]:
                    break
                time.sleep(0.05)
            break

        time.sleep(0.05)

    took = time.time() - t0
    final_result = (state["result"] or "").strip() or None
    logger.info(f"[ASR] Took {took:.3f}s, result={bool(state['result'])}, done={state['done']}")
    logger.info(f"[ASR] 辨識結果: '{final_result}'")
    return final_result


def asr_fallback_openai(wav16k_bytes: bytes) -> Optional[str]:
    """
    使用 OpenAI Whisper 作為備援 ASR

    Args:
        wav16k_bytes: 16kHz mono WAV 音檔

    Returns:
        辨識出的文字，失敗則返回 None
    """
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.warning("[ASR-FB] No OpenAI API key")
            return None

        client = OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"[ASR-FB] OpenAI init failed: {e}")
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav16k_bytes)
        f.flush()
        path = f.name

    try:
        # 嘗試 gpt-4o-transcribe
        try:
            with open(path, "rb") as fh:
                resp = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=fh
                )
            text = (resp.text or "").strip()
            if text:
                logger.info(f"[ASR-FB] gpt-4o-transcribe 辨識結果: '{text}'")
                return text
            else:
                logger.warning("[ASR-FB] gpt-4o-transcribe returned empty text")
        except Exception as e:
            logger.warning(f"[ASR-FB] gpt-4o-transcribe failed: {e}")

        # 嘗試 whisper-1
        try:
            with open(path, "rb") as fh:
                resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=fh
                )
            text = (resp.text or "").strip()
            if text:
                logger.info(f"[ASR-FB] whisper-1 辨識結果: '{text}'")
                return text
            else:
                logger.warning("[ASR-FB] whisper-1 returned empty text")
        except Exception as e:
            logger.warning(f"[ASR-FB] whisper-1 failed: {e}")

        return None
    finally:
        try:
            os.unlink(path)
        except:
            pass
