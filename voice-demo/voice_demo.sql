-- link nghe thử cho giọng VieNeu (file trong web-vi/voice-demo)
SET NAMES utf8mb4;
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_01.mp3' WHERE id = 'TTS_VieNeu_01';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_02.mp3' WHERE id = 'TTS_VieNeu_02';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_03.mp3' WHERE id = 'TTS_VieNeu_03';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_04.mp3' WHERE id = 'TTS_VieNeu_04';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_05.mp3' WHERE id = 'TTS_VieNeu_05';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_06.mp3' WHERE id = 'TTS_VieNeu_06';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_07.mp3' WHERE id = 'TTS_VieNeu_07';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_08.mp3' WHERE id = 'TTS_VieNeu_08';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_09.mp3' WHERE id = 'TTS_VieNeu_09';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_10.mp3' WHERE id = 'TTS_VieNeu_10';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_11.mp3' WHERE id = 'TTS_VieNeu_11';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_12.mp3' WHERE id = 'TTS_VieNeu_12';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_13.mp3' WHERE id = 'TTS_VieNeu_13';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_14.mp3' WHERE id = 'TTS_VieNeu_14';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_15.mp3' WHERE id = 'TTS_VieNeu_15';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_16.mp3' WHERE id = 'TTS_VieNeu_16';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_17.mp3' WHERE id = 'TTS_VieNeu_17';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_18.mp3' WHERE id = 'TTS_VieNeu_18';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_19.mp3' WHERE id = 'TTS_VieNeu_19';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_20.mp3' WHERE id = 'TTS_VieNeu_20';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_21.mp3' WHERE id = 'TTS_VieNeu_21';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_22.mp3' WHERE id = 'TTS_VieNeu_22';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_23.mp3' WHERE id = 'TTS_VieNeu_23';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_24.mp3' WHERE id = 'TTS_VieNeu_24';
UPDATE ai_tts_voice SET voice_demo = 'https://xiaozhi.minizjp.com/voice-demo/TTS_VieNeu_25.mp3' WHERE id = 'TTS_VieNeu_25';
SELECT id, name, voice_demo FROM ai_tts_voice WHERE tts_model_id = 'TTS_VieNeuTTS' ORDER BY sort;

