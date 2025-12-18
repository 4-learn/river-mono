import argparse, io, os, base64, tempfile, platform, subprocess, requests, sys, time
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf

SR=16000; CH=1; DTYPE='int16'

def push_to_talk_bytes():
    print("🔴 Enter 開始，Enter 結束")
    input(); print("🎙️ 錄音中…")
    frames=[]
    def cb(indata, f, ti, st): frames.append(indata.copy())
    stream = sd.InputStream(samplerate=SR, channels=CH, dtype=DTYPE, callback=cb)
    stream.start(); input(); stream.stop(); stream.close()
    audio = np.concatenate(frames, axis=0) if frames else np.zeros((1,CH), dtype=DTYPE)
    with io.BytesIO() as buf:
        sf.write(buf, audio, SR, format='WAV', subtype='PCM_16')
        return buf.getvalue()

def play_wav_bytes(b):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b); path=f.name
    try:
        sysname=platform.system()
        if sysname=="Darwin": subprocess.run(["afplay", path], check=True)
        elif sysname=="Linux": subprocess.run(["aplay", path], check=True)
        elif sysname=="Windows":
            import winsound; winsound.PlaySound(path, winsound.SND_FILENAME)
    finally:
        try: os.unlink(path)
        except: pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--mode", choices=["full","fast"], default="fast")
    ap.add_argument("--save", action="store_true", help="保存錄音 wav 文件")
    ap.add_argument("--save-dir", default="recordings", help="保存錄音的目錄")
    args=ap.parse_args()

    wav=push_to_talk_bytes()

    # 保存錄音
    if args.save:
        os.makedirs(args.save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(args.save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(wav)
        print(f"💾 已保存錄音：{filepath}")
    if args.mode=="full":
        r=requests.post(args.server.rstrip("/")+"/dialogue", files={"file":("mic.wav", wav, "audio/wav")}, timeout=120)
        r.raise_for_status(); data=r.json()
        print("ASR：", data.get("text"))
        print("AI ：", data.get("response"))
        print("timings：", data.get("timings"))
        b64=data.get("audio_wav_base64") or ""
        if b64: play_wav_bytes(base64.b64decode(b64))
        return

    # fast
    r=requests.post(args.server.rstrip("/")+"/dialogue_fast", files={"file":("mic.wav", wav, "audio/wav")}, timeout=120)
    r.raise_for_status(); data=r.json()
    print("ASR：", data.get("text"))
    print("AI ：", data.get("response"))
    print("timings(no-tts)：", data.get("timings"))
    job=data.get("job_id")
    print("🎧 等待音檔… job =", job)
    url=args.server.rstrip("/")+"/audio/"+job
    t0=time.time()
    while True:
        rr=requests.get(url, timeout=10)
        rr.raise_for_status()
        d=rr.json()
        if d.get("ready"):
            print(f"音檔就緒，用時 {time.time()-t0:.2f}s")
            b64=d.get("audio_wav_base64") or ""
            if b64: play_wav_bytes(base64.b64decode(b64))
            break
        time.sleep(0.25)

if __name__=="__main__":
    main()
