"""Minimal OpenAI-compatible ASR server (POST /v1/audio/transcriptions) for xiaozhi-server.
Runs Whisper on the local GPU via transformers. Env:
  ASR_MODEL (default openai/whisper-large-v3-turbo)  ASR_LANGUAGE (default vi, "auto" = detect)
  ASR_API_KEY (optional Bearer key)  HOST/PORT (default 0.0.0.0:8011)
"""
import io, os, re, time, wave, logging
import numpy as np, torch, uvicorn
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from transformers import pipeline

MODEL = os.environ.get("ASR_MODEL", "openai/whisper-large-v3-turbo")
LANG = os.environ.get("ASR_LANGUAGE", "vi")
KEY = os.environ.get("ASR_API_KEY")
log = logging.getLogger("asr"); logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

device = "cuda:0" if torch.cuda.is_available() else "cpu"
log.info("loading %s on %s", MODEL, device)
asr = pipeline("automatic-speech-recognition", model=MODEL, device=device,
               torch_dtype=torch.float16 if device != "cpu" else torch.float32)
app = FastAPI()

# Đa ngôn ngữ: ALT_MODEL (vd whisper-large-v3-turbo) đoán ngôn ngữ từng câu; ngôn ngữ trong ALT_LANGS
# (vd "ja") thì ALT_MODEL nhận dạng luôn, còn lại dùng ASR_MODEL chính (PhoWhisper cho tiếng Việt).
ALT_MODEL = os.environ.get("ALT_MODEL")
ALT_LANGS = {x.strip() for x in os.environ.get("ALT_LANGS", "ja").split(",") if x.strip()}
alt = None
if ALT_MODEL:
    log.info("loading language detector / alt model %s for %s", ALT_MODEL, sorted(ALT_LANGS))
    alt = pipeline("automatic-speech-recognition", model=ALT_MODEL, device=device,
                   torch_dtype=torch.float16 if device != "cpu" else torch.float32)


def lang_probs(audio: np.ndarray) -> dict:
    """Xác suất từng ngôn ngữ Whisper ({'vi': 0.9, 'ja': 0.05, …}) của 30 giây đầu."""
    gc = alt.model.generation_config
    feats = alt.feature_extractor(audio, sampling_rate=16000, return_tensors="pt").input_features
    feats = feats.to(alt.model.device, dtype=alt.model.dtype)
    codes = list(gc.lang_to_id.keys())
    ids = torch.tensor([gc.lang_to_id[c] for c in codes], device=alt.model.device)
    sot = torch.tensor([[gc.decoder_start_token_id]], device=alt.model.device)
    with torch.inference_mode():
        logits = alt.model(input_features=feats, decoder_input_ids=sot).logits[0, -1]
        p = torch.softmax(logits[ids].float(), dim=-1).cpu().numpy()
    return {c[2:-2]: float(x) for c, x in zip(codes, p)}


# Chế độ tiếng Nhật (xiaozhi gửi model có đuôi "|ja" khi agent dùng TTS VOICEVOX): mặc định nhận dạng
# tiếng Nhật, chỉ chuyển sang PhoWhisper khi CHẮC CHẮN là tiếng Việt (xác suất >= JA_MODE_VI_CONF).
JA_MODE_VI_CONF = float(os.environ.get("JA_MODE_VI_CONF", "0.8"))

# Whisper "hallucinations": on silence/noise it invents YouTube outro lines learned from subtitles.
# Any transcript matching these is treated as "nothing was said" (returns empty text).
HALLUCINATIONS = re.compile("|".join([
    r"subscribe", r"ghiền mì gõ", r"đăng ký kênh", r"đăng kí kênh", r"bấm đăng ký", r"nhấn đăng ký",
    r"không bỏ lỡ những video", r"theo dõi kênh", r"cảm ơn các bạn đã (theo dõi|xem|lắng nghe)",
    r"hẹn gặp lại các bạn trong", r"video (tiếp theo|hấp dẫn)", r"like,? share", r"la la school",
    r"amara\.org", r"phụ đề (được thực hiện|bởi)", r"subtitles? by",
    # tiếng Nhật
    r"ご視聴(いただき)?ありがとうございま", r"チャンネル登録", r"高評価", r"次回の動画", r"字幕(制作|提供|作成)",
]), re.IGNORECASE)
MIN_RMS_DBFS = float(os.environ.get("ASR_MIN_DBFS", "-50"))  # quieter than this = silence


def rms_dbfs(a: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9) if len(a) else -120.0


def read_wav(data: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(data)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise HTTPException(400, "only 16-bit PCM wav supported")
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != 16000:  # simple linear resample
        n = int(len(a) * 16000 / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return a


@app.post("/v1/audio/transcriptions")
async def transcribe(file: UploadFile = File(...), model: str = Form(None), language: str = Form(None),
                     authorization: str = Header(None)):
    if KEY and authorization != f"Bearer {KEY}":
        raise HTTPException(401, "bad api key")
    audio = read_wav(await file.read())
    lang = language or LANG
    kw = {"task": "transcribe"}
    if lang and lang != "auto":
        kw["language"] = lang
    level = rms_dbfs(audio)
    if level < MIN_RMS_DBFS:
        log.info("%.2fs audio, %.1f dBFS -> skipped (silence)", len(audio) / 16000, level)
        return {"text": ""}
    t0 = time.perf_counter()
    engine, detected, mode = asr, None, "vi"
    if alt is not None:
        probs = lang_probs(audio)
        detected = max(probs, key=probs.get)
        mode = "ja" if (model or "").lower().endswith("|ja") else "vi"
        if mode == "ja":
            # Nhật là chính: chỉ dùng PhoWhisper khi chắc chắn là tiếng Việt
            if detected == "vi" and probs["vi"] >= JA_MODE_VI_CONF:
                kw = {"task": "transcribe", "language": "vi"}
            else:
                engine, kw = alt, {"task": "transcribe", "language": "ja"}
        elif detected in ALT_LANGS:
            engine, kw = alt, {"task": "transcribe", "language": detected}
        log.info("mode=%s language=%s (vi=%.2f ja=%.2f) -> %s", mode, detected, probs.get("vi", 0),
                 probs.get("ja", 0), "alt" if engine is alt else "main")
    with torch.inference_mode():
        text = engine({"raw": audio, "sampling_rate": 16000}, generate_kwargs=kw)["text"].strip()
    if HALLUCINATIONS.search(text):
        log.info("%.2fs audio, %.1f dBFS -> DROPPED hallucination | %s", len(audio) / 16000, level, text)
        return {"text": ""}
    log.info("%.2fs audio, %.1f dBFS -> %.2fs | %s", len(audio) / 16000, level, time.perf_counter() - t0, text)
    return {"text": text}


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "device": device, "language": LANG}


if __name__ == "__main__":
    # warm-up so the first real request is fast
    asr({"raw": np.zeros(16000, dtype=np.float32), "sampling_rate": 16000}, generate_kwargs={"language": "vi"})
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8011")))
