"""TTS router Việt/Nhật cho xiaozhi (API giống OpenAI /v1/audio/speech).

Tách câu thành các đoạn theo ngôn ngữ:
  - đoạn có chữ Nhật (hiragana/katakana/kanji) -> VOICEVOX
  - còn lại (tiếng Việt/Anh)                  -> VieNeu-TTS
rồi ghép thành 1 file WAV 24 kHz mono. xiaozhi gọi router này thay cho VieNeu.
Hai chế độ (chọn theo "model" trong request):
  - model bắt đầu bằng "voicevox": TIẾNG NHẬT LÀ CHÍNH. voice = id giọng VOICEVOX ("3" hoặc "3|vi=Mai Anh").
    Chỉ đoạn có chữ tiếng Việt có dấu mới chuyển sang VieNeu (giọng VI_VOICE); chữ Latin khác (OK, AI...) VOICEVOX đọc.
  - còn lại: TIẾNG VIỆT LÀ CHÍNH. voice = giọng VieNeu; đoạn chữ Nhật đọc bằng JA_SPEAKER (hoặc "Mai Anh|ja=3").
"""
import io, os, re, wave, logging
import numpy as np, httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

VIENEU_URL = os.environ.get("VIENEU_URL", "http://host.docker.internal:8010/v1/audio/speech")
VIENEU_KEY = os.environ.get("VIENEU_KEY", "vieneu-local-key")
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://voicevox:50021").rstrip("/")
JA_SPEAKER = int(os.environ.get("JA_SPEAKER", "3"))
VI_VOICE = os.environ.get("VI_VOICE", "Mai Anh")
API_KEY = os.environ.get("ROUTER_KEY", "vieneu-local-key")
SR = 24000
TARGET_DBFS = float(os.environ.get("TARGET_DBFS", "-18"))  # chuẩn hoá âm lượng mọi đoạn (VOICEVOX vốn nhỏ hơn VieNeu ~5 dB)
log = logging.getLogger("tts-router")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = FastAPI(docs_url=None, redoc_url=None)
client = httpx.Client(timeout=60)

JA = re.compile(r"[぀-ヿㇰ-ㇿ一-鿿ｦ-ﾟ々ー]")
VI_CHARS = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.I)
JA_PUNCT = set("。、「」『』！？・…〜ー（）")


def split_lang(text):
    """[(lang, đoạn)] - ký tự trung tính (số, dấu cách, dấu câu) đi theo đoạn đang mở."""
    segs, cur, buf = [], None, ""
    for ch in text:
        lang = "ja" if (JA.match(ch) or ch in JA_PUNCT) else ("vi" if ch.isalpha() else None)
        if lang and cur and lang != cur:
            segs.append((cur, buf)); buf = ""
        if lang:
            cur = lang
        buf += ch
    if buf.strip():
        segs.append((cur or "vi", buf))
    # gộp đoạn quá ngắn (chỉ dấu câu) vào đoạn trước
    out = []
    for lang, s in segs:
        if out and not re.search(r"\w", s):
            out[-1] = (out[-1][0], out[-1][1] + s)
        else:
            out.append((lang, s))
    return [(l, s.strip(" \"'()[]{}「」『』")) for l, s in out if re.search(r"\w", s)]


def ja_primary(segs):
    """Chế độ Nhật là chính: đoạn Latin không có dấu tiếng Việt -> VOICEVOX; gộp các đoạn liền kề cùng ngôn ngữ."""
    out = []
    for lang, s in segs:
        if lang == "vi" and not VI_CHARS.search(s):
            lang = "ja"
        if out and out[-1][0] == lang:
            out[-1] = (lang, out[-1][1] + " " + s)
        else:
            out.append((lang, s))
    return out


def wav_to_pcm(data):
    with wave.open(io.BytesIO(data)) as w:
        sr, ch, raw = w.getframerate(), w.getnchannels(), w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SR and len(a):
        n = int(len(a) * SR / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    return a.astype(np.int16)


def vieneu(text, voice):
    body = {"model": "vieneu-v3-turbo", "input": text, "response_format": "pcm", "sample_rate": SR}
    if voice:
        body["voice"] = voice
    r = client.post(VIENEU_URL, json=body, headers={"Authorization": f"Bearer {VIENEU_KEY}"})
    r.raise_for_status()
    return np.frombuffer(r.content[: len(r.content) // 2 * 2], dtype=np.int16)


def voicevox(text, speaker):
    q = client.post(f"{VOICEVOX_URL}/audio_query", params={"text": text, "speaker": speaker})
    q.raise_for_status()
    query = q.json()
    query["outputSamplingRate"] = SR
    s = client.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": speaker}, json=query)
    s.raise_for_status()
    return wav_to_pcm(s.content)


def normalize(pcm):
    """Đưa độ to (RMS phần có tiếng) về TARGET_DBFS, chặn đỉnh mềm bằng tanh để không bị rè."""
    a = pcm.astype(np.float32)
    voiced = a[np.abs(a) > 300]
    if len(voiced) < SR // 20:
        return pcm
    rms = np.sqrt(np.mean(voiced ** 2))
    gain = min(10 ** (TARGET_DBFS / 20) * 32768 / rms, 4.0)
    lim = 32767 * 0.97
    return (lim * np.tanh(a * gain / lim)).astype(np.int16)


class SpeechReq(BaseModel):
    input: str
    voice: str | None = None
    model: str | None = None
    response_format: str | None = "wav"
    speed: float | None = None


@app.post("/v1/audio/speech")
def speech(req: SpeechReq, authorization: str = Header(None)):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(401, "bad api key")
    voice, ja_speaker = (req.voice or "").strip(), JA_SPEAKER
    segs = split_lang(req.input)
    if (req.model or "").lower().startswith("voicevox"):
        m = re.match(r"^(?:ja=)?(\d+)(?:\|vi=(.+))?$", voice)
        ja_speaker = int(m.group(1)) if m else JA_SPEAKER
        voice = (m.group(2) if m and m.group(2) else VI_VOICE)
        segs = ja_primary(segs)
    else:
        m = re.match(r"^(.*?)\|ja=(\d+)$", voice)
        if m:
            voice, ja_speaker = m.group(1), int(m.group(2))
    parts = []
    gap = np.zeros(int(SR * 0.12), dtype=np.int16)
    for lang, seg in segs:
        pcm = voicevox(seg, ja_speaker) if lang == "ja" else vieneu(seg, voice or None)
        if parts:
            parts.append(gap)
        parts.append(normalize(pcm))
        log.info("%s | %s", lang, seg[:60])
    pcm = np.concatenate(parts) if parts else np.zeros(SR // 10, dtype=np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return Response(buf.getvalue(), media_type="audio/wav")


@app.get("/health")
def health():
    try:
        v = client.get(f"{VOICEVOX_URL}/version", timeout=3).text
    except Exception as e:
        v = f"ERR {e}"
    return {"ok": True, "voicevox": v, "ja_speaker": JA_SPEAKER, "vi_voice": VI_VOICE}


@app.get("/voicevox/speakers")
def speakers():
    data = client.get(f"{VOICEVOX_URL}/speakers").json()
    return JSONResponse([{"name": s["name"], "styles": [{"id": st["id"], "name": st["name"]} for st in s["styles"]]}
                         for s in data])
