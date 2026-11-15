"""Tạo file nghe thử cho 25 giọng VieNeu (mỗi giọng đọc 1 câu giới thiệu) + SQL gắn link voice_demo."""
import json, os, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://xiaozhi.minizjp.com/voice-demo/"
VOICES = ["Hải Đăng", "Mai Anh", "Ngọc Huyền", "Trúc Ly", "Quỳnh Anh", "Thùy Dung", "Ngọc Trân", "Ngọc Linh",
          "Đoan Trang", "Thục Đoan", "Mỹ Duyên", "Kim Thanh", "Thiện Minh", "Quang Sơn", "Minh Đức", "Thái Sơn",
          "Xuân Vĩnh", "Thanh Bình", "Minh Triết", "Đức Trí", "Quốc Tuấn", "Phạm Tuyên", "Thiền Tâm Đức", "Adam",
          "Adam bựa"]

def tts(text, voice):
    body = {"model": "vieneu-v3-turbo", "input": text, "voice": voice, "response_format": "wav", "sample_rate": 24000}
    req = urllib.request.Request("http://127.0.0.1:8010/v1/audio/speech", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer vieneu-local-key", "Content-Type": "application/json"})
    d = bytearray(urllib.request.urlopen(req, timeout=120).read())
    n = len(d) - 44  # sửa header "không rõ độ dài" thành file wav chuẩn để trình duyệt tua được
    d[4:8] = (36 + n).to_bytes(4, "little"); d[40:44] = n.to_bytes(4, "little")
    return bytes(d)

sql = ["-- link nghe thử cho giọng VieNeu (file trong web-vi/voice-demo)", "SET NAMES utf8mb4;"]
for i, v in enumerate(VOICES, 1):
    vid = f"TTS_VieNeu_{i:02d}"
    text = ("Hi, I'm Adam. Nice to meet you, let's have a chat!" if v == "Adam"
            else f"Xin chào, mình là {v}. Rất vui được trò chuyện cùng bạn hôm nay!")
    data = tts(text, v)
    open(os.path.join(OUT, vid + ".wav"), "wb").write(data)
    sql.append(f"UPDATE ai_tts_voice SET voice_demo = '{BASE_URL}{vid}.wav' WHERE id = '{vid}';")
    print(f"{vid} {v}: {len(data)//1024} KB")
sql.append("SELECT id, name, voice_demo FROM ai_tts_voice WHERE tts_model_id = 'TTS_VieNeuTTS' ORDER BY sort;")
open(os.path.join(OUT, "voice_demo.sql"), "w", encoding="utf-8").write("\n".join(sql) + "\n")
