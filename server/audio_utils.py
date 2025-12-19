import subprocess
import logging
import time

logger = logging.getLogger("uvicorn")


def ffmpeg_to_wav16k_mono(raw_bytes: bytes) -> bytes:
    """
    使用 FFmpeg 將任何音訊格式轉換為 16kHz mono WAV
    並移除尾端靜音

    Args:
        raw_bytes: 原始音訊檔案的 bytes

    Returns:
        轉換後的 WAV 音檔 bytes

    Raises:
        RuntimeError: 如果 FFmpeg 執行失敗
    """
    t0 = time.time()

    try:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-i", "pipe:0",  # 從 stdin 讀取
                "-ar", "16000",  # 採樣率 16kHz
                "-ac", "1",      # 單聲道
                "-f", "wav",     # 輸出格式 WAV
                "pipe:1"         # 輸出到 stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate(input=raw_bytes)

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')[:200]
            raise RuntimeError(f"FFmpeg failed: {error_msg}")

        took = time.time() - t0
        logger.info(f"[FFmpeg] Converted in {took:.3f}s | input={len(raw_bytes)}B output={len(stdout)}B")

        return stdout

    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install ffmpeg: sudo apt install ffmpeg")
    except Exception as e:
        raise RuntimeError(f"FFmpeg error: {e}")
