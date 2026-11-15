import httpx
ASR = "http://host.docker.internal:8012/v1/audio/transcriptions"
AH = {"Authorization": "Bearer local-asr-key"}
for model in ["PhoWhisper-medium", "PhoWhisper-medium|ja"]:
    for f in ["ja", "vi", "mix"]:
        with open(f"/tmp/{f}.wav", "rb") as fh:
            r = httpx.post(ASR, headers=AH, files={"file": ("a.wav", fh, "audio/wav")}, data={"model": model}, timeout=120)
        print(f"{model:22s} {f:4s} -> {r.json().get('text')}")
