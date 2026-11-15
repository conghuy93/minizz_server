import httpx, time, json
H = {"Authorization": "Bearer vieneu-local-key"}
ASR = "http://host.docker.internal:8012/v1/audio/transcriptions"
AH = {"Authorization": "Bearer local-asr-key"}

def tts(text, name):
    t = time.time()
    r = httpx.post("http://localhost:8020/v1/audio/speech", headers=H,
                   json={"model": "vieneu", "input": text, "voice": "", "response_format": "wav"}, timeout=120)
    r.raise_for_status()
    open(f"/tmp/{name}.wav", "wb").write(r.content)
    print(f"TTS {name}: {len(r.content)} bytes, {time.time()-t:.2f}s")
    return f"/tmp/{name}.wav"

def asr(path):
    t = time.time()
    with open(path, "rb") as f:
        r = httpx.post(ASR, headers=AH, files={"file": ("a.wav", f, "audio/wav")},
                       data={"model": "whisper"}, timeout=120)
    print(f"ASR {path}: {r.status_code} {r.text[:200]} ({time.time()-t:.2f}s)")

a = tts("Con vịt tiếng Nhật là アヒル nhé! Chào buổi sáng là おはようございます.", "mix")
b = tts("こんにちは、今日はとても良い天気ですね。一緒に散歩に行きましょう。", "ja")
c = tts("Xin chào, hôm nay trời rất đẹp, mình cùng đi dạo nhé.", "vi")
asr(b)
asr(c)
