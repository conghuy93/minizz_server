"""Chạy TRONG container xiaozhi-tts-router: tạo voicevox.sql + file wav nghe thử vào /tmp/vv/."""
import httpx, json, os
H = {"Authorization": "Bearer vieneu-local-key"}
EXTRA = {0, 6, 1, 7, 15, 18, 22}  # thêm vài style nổi tiếng: めたん/ずんだもん/そら あまあま, ツンツン, ささやき
SAMPLE = "こんにちは！私の声はこんな感じだよ。これからよろしくね！"
sp = httpx.get("http://voicevox:50021/speakers", timeout=30).json()
voices = []
for s in sp:
    for i, st in enumerate(s["styles"]):
        if i == 0 or st["id"] in EXTRA:
            name = s["name"] if i == 0 else f'{s["name"]}・{st["name"]}'
            voices.append((st["id"], name[:20], s["name"]))
os.makedirs("/tmp/vv", exist_ok=True)
rows = []
for n, (sid, name, char) in enumerate(voices, 1):
    vid = f"TTS_VV_{sid:03d}"
    r = httpx.post("http://localhost:8020/v1/audio/speech", headers=H, timeout=120,
                   json={"model": "voicevox", "input": SAMPLE, "voice": str(sid)})
    r.raise_for_status()
    open(f"/tmp/vv/{vid}.wav", "wb").write(r.content)
    esc = lambda x: x.replace("'", "''")
    rows.append(f"('{vid}','TTS_VoiceVox','{esc(name)}','{sid}','Tiếng Nhật',"
                f"'https://xiaozhi.minizjp.com/voice-demo/{vid}.mp3','VOICEVOX:{esc(char)}',{n},NOW())")
    print(vid, name)
sql = f"""-- Mô hình TTS tiếng Nhật (VOICEVOX qua tts-router, Nhật là chính, đoạn tiếng Việt đọc bằng VieNeu)
DELETE FROM ai_model_config WHERE id='TTS_VoiceVox';
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, sort, create_date)
VALUES ('TTS_VoiceVox','TTS','VoiceVoxTTS','VOICEVOX (Tiếng Nhật, local)',0,1,
 JSON_OBJECT('type','openai','model','voicevox','voice','3','speed',1,'format','wav','api_key','vieneu-local-key',
  'api_url','http://xiaozhi-tts-router:8020/v1/audio/speech','output_dir','tmp/'),1,NOW());
DELETE FROM ai_tts_voice WHERE tts_model_id='TTS_VoiceVox';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, create_date) VALUES
{(','+chr(10)).join(rows)};
"""
open("/tmp/vv/voicevox.sql", "w", encoding="utf-8").write(sql)
print(len(rows), "voices")
