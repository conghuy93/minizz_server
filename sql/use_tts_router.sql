-- Chuyển TTS VieNeu sang tts-router (Việt -> VieNeu, Nhật -> VOICEVOX)
UPDATE ai_model_config
SET config_json = JSON_SET(config_json, '$.api_url', 'http://xiaozhi-tts-router:8020/v1/audio/speech')
WHERE id = 'TTS_VieNeuTTS';
SELECT id, JSON_EXTRACT(config_json, '$.api_url') FROM ai_model_config WHERE id = 'TTS_VieNeuTTS';
