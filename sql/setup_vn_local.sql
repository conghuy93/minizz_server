-- Vietnamese setup: Gemini (OpenAI-compatible) LLM/VLLM, local VieNeu-TTS, local Whisper ASR
-- Re-runnable. Services on the Windows host are reached from Docker via host.docker.internal.
SET NAMES utf8mb4;

DELETE FROM ai_model_config WHERE id IN ('LLM_GeminiOpenAI','VLLM_GeminiVLLM','TTS_VieNeuTTS','ASR_LocalWhisper');
DELETE FROM ai_tts_voice WHERE tts_model_id = 'TTS_VieNeuTTS';

INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, remark, sort, create_date, update_date) VALUES
('LLM_GeminiOpenAI', 'LLM', 'GeminiOpenAI', 'Gemini 3.5 Flash-Lite', 1, 1,
 JSON_OBJECT('type','openai','base_url','https://generativelanguage.googleapis.com/v1beta/openai/',
             'model_name','gemini-3.5-flash-lite','api_key','<GEMINI_API_KEY>'),
 'Gemini qua endpoint tuong thich OpenAI', 0, NOW(), NOW()),
('VLLM_GeminiVLLM', 'VLLM', 'GeminiVLLM', 'Gemini 3.5 Flash-Lite (vision)', 1, 1,
 JSON_OBJECT('type','openai','base_url','https://generativelanguage.googleapis.com/v1beta/openai/',
             'model_name','gemini-3.5-flash-lite','api_key','<GEMINI_API_KEY>'),
 'Gemini vision', 0, NOW(), NOW()),
('TTS_VieNeuTTS', 'TTS', 'VieNeuTTS', 'VieNeu-TTS v3 Turbo (local GPU)', 1, 1,
 JSON_OBJECT('type','openai','api_url','http://host.docker.internal:8010/v1/audio/speech','api_key','vieneu-local-key',
             'model','vieneu-v3-turbo','voice','Hải Đăng','speed',1,'format','wav','output_dir','tmp/'),
 'F:\\VieNeu-TTS\\start_api_gpu.bat (port 8010)', 0, NOW(), NOW()),
('ASR_LocalWhisper', 'ASR', 'LocalWhisper', 'Whisper large-v3-turbo (local GPU, vi)', 1, 1,
 JSON_OBJECT('type','openai','base_url','http://host.docker.internal:8011/v1/audio/transcriptions','api_key','local-asr-key',
             'model_name','whisper-large-v3-turbo','output_dir','tmp/'),
 'F:\\whisper-asr\\start_asr_gpu.bat (port 8011)', 0, NOW(), NOW());

-- only one default per type
UPDATE ai_model_config SET is_default = 0 WHERE model_type = 'LLM'  AND id <> 'LLM_GeminiOpenAI';
UPDATE ai_model_config SET is_default = 0 WHERE model_type = 'VLLM' AND id <> 'VLLM_GeminiVLLM';
UPDATE ai_model_config SET is_default = 0 WHERE model_type = 'TTS'  AND id <> 'TTS_VieNeuTTS';
UPDATE ai_model_config SET is_default = 0 WHERE model_type = 'ASR'  AND id <> 'ASR_LocalWhisper';
-- function calling (weather, music, IoT tools) works with Gemini
UPDATE ai_model_config SET is_default = (id = 'Intent_function_call') WHERE model_type = 'Intent';

INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, sort, create_date) VALUES
('TTS_VieNeu_01','TTS_VieNeuTTS','Hải Đăng','Hải Đăng','Tiếng Việt',1,NOW()),
('TTS_VieNeu_02','TTS_VieNeuTTS','Mai Anh','Mai Anh','Tiếng Việt',2,NOW()),
('TTS_VieNeu_03','TTS_VieNeuTTS','Ngọc Huyền','Ngọc Huyền','Tiếng Việt',3,NOW()),
('TTS_VieNeu_04','TTS_VieNeuTTS','Trúc Ly','Trúc Ly','Tiếng Việt',4,NOW()),
('TTS_VieNeu_05','TTS_VieNeuTTS','Quỳnh Anh','Quỳnh Anh','Tiếng Việt',5,NOW()),
('TTS_VieNeu_06','TTS_VieNeuTTS','Thùy Dung','Thùy Dung','Tiếng Việt',6,NOW()),
('TTS_VieNeu_07','TTS_VieNeuTTS','Ngọc Trân','Ngọc Trân','Tiếng Việt',7,NOW()),
('TTS_VieNeu_08','TTS_VieNeuTTS','Ngọc Linh','Ngọc Linh','Tiếng Việt',8,NOW()),
('TTS_VieNeu_09','TTS_VieNeuTTS','Đoan Trang','Đoan Trang','Tiếng Việt',9,NOW()),
('TTS_VieNeu_10','TTS_VieNeuTTS','Thục Đoan','Thục Đoan','Tiếng Việt',10,NOW()),
('TTS_VieNeu_11','TTS_VieNeuTTS','Mỹ Duyên','Mỹ Duyên','Tiếng Việt',11,NOW()),
('TTS_VieNeu_12','TTS_VieNeuTTS','Kim Thanh','Kim Thanh','Tiếng Việt',12,NOW()),
('TTS_VieNeu_13','TTS_VieNeuTTS','Thiện Minh','Thiện Minh','Tiếng Việt',13,NOW()),
('TTS_VieNeu_14','TTS_VieNeuTTS','Quang Sơn','Quang Sơn','Tiếng Việt',14,NOW()),
('TTS_VieNeu_15','TTS_VieNeuTTS','Minh Đức','Minh Đức','Tiếng Việt',15,NOW()),
('TTS_VieNeu_16','TTS_VieNeuTTS','Thái Sơn','Thái Sơn','Tiếng Việt',16,NOW()),
('TTS_VieNeu_17','TTS_VieNeuTTS','Xuân Vĩnh','Xuân Vĩnh','Tiếng Việt',17,NOW()),
('TTS_VieNeu_18','TTS_VieNeuTTS','Thanh Bình','Thanh Bình','Tiếng Việt',18,NOW()),
('TTS_VieNeu_19','TTS_VieNeuTTS','Minh Triết','Minh Triết','Tiếng Việt',19,NOW()),
('TTS_VieNeu_20','TTS_VieNeuTTS','Đức Trí','Đức Trí','Tiếng Việt',20,NOW()),
('TTS_VieNeu_21','TTS_VieNeuTTS','Quốc Tuấn','Quốc Tuấn','Tiếng Việt',21,NOW()),
('TTS_VieNeu_22','TTS_VieNeuTTS','Phạm Tuyên','Phạm Tuyên','Tiếng Việt',22,NOW()),
('TTS_VieNeu_23','TTS_VieNeuTTS','Thiền Tâm Đức','Thiền Tâm Đức','Tiếng Việt',23,NOW()),
('TTS_VieNeu_24','TTS_VieNeuTTS','Adam','Adam','English',24,NOW()),
('TTS_VieNeu_25','TTS_VieNeuTTS','Adam bựa','Adam bựa','Tiếng Việt',25,NOW());

-- addresses handed to devices (LAN IP of this PC)
UPDATE sys_params SET param_value = 'ws://<LAN_IP>:8000/xiaozhi/v1/' WHERE param_code = 'server.websocket';
UPDATE sys_params SET param_value = 'http://<LAN_IP>:8002/xiaozhi/ota/' WHERE param_code = 'server.ota';

SELECT id, model_type, is_default FROM ai_model_config WHERE is_default = 1 ORDER BY model_type;
SELECT COUNT(*) AS vieneu_voices FROM ai_tts_voice WHERE tts_model_id = 'TTS_VieNeuTTS';

-- Agent templates decide what the server loads at startup and what new agents start with
UPDATE ai_agent_template SET asr_model_id = 'ASR_LocalWhisper', llm_model_id = 'LLM_GeminiOpenAI',
       vllm_model_id = 'VLLM_GeminiVLLM', tts_model_id = 'TTS_VieNeuTTS', tts_voice_id = 'TTS_VieNeu_01',
       intent_model_id = 'Intent_function_call';
SELECT agent_name, asr_model_id, llm_model_id, tts_model_id, tts_voice_id FROM ai_agent_template ORDER BY sort;
