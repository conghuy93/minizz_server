-- PhoWhisper-medium (VinAI) as an optional ASR, served by F:\whisper-asr\start_phowhisper_gpu.bat on port 8012
SET NAMES utf8mb4;
DELETE FROM ai_model_config WHERE id = 'ASR_PhoWhisper';
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, remark, sort, create_date, update_date) VALUES
('ASR_PhoWhisper', 'ASR', 'PhoWhisper', 'PhoWhisper-medium (local GPU, vi, khuyên dùng)', 0, 1,
 JSON_OBJECT('type','openai','base_url','http://host.docker.internal:8012/v1/audio/transcriptions','api_key','local-asr-key',
             'model_name','PhoWhisper-medium','output_dir','tmp/'),
 'F:\\whisper-asr\\start_phowhisper_gpu.bat (port 8012). ~0.85s/câu, chính xác hơn Whisper turbo.', 1, NOW(), NOW());
SELECT id, model_name, is_default FROM ai_model_config WHERE model_type = 'ASR' AND id IN ('ASR_LocalWhisper','ASR_PhoWhisper');

