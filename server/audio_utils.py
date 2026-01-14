import subprocess
import logging
import time

logger = logging.getLogger("uvicorn")


def ffmpeg_to_wav16k_mono(raw_bytes: bytes) -> bytes:
    """
    使用 FFmpeg 將任何音訊格式轉換為 16kHz mono WAV

    Args:
        raw_bytes: 原始音訊檔案的 bytes

    Returns:
        轉換後的 WAV 音檔 bytes
    """
    t0 = time.time()

    try:
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-i', 'pipe:0',
                '-ar', '16000',
                '-ac', '1',
                '-f', 'wav',
                'pipe:1'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate(input=raw_bytes)

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')[:200]
            raise RuntimeError(f'FFmpeg failed: {error_msg}')

        took = time.time() - t0
        logger.info(f'[FFmpeg] Converted in {took:.3f}s | input={len(raw_bytes)}B output={len(stdout)}B')

        return stdout

    except FileNotFoundError:
        raise RuntimeError('FFmpeg not found')
    except Exception as e:
        raise RuntimeError(f'FFmpeg error: {e}')
