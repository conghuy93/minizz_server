-- Make PhoWhisper-medium the only ASR (Whisper turbo removed)
SET NAMES utf8mb4;
UPDATE ai_agent          SET asr_model_id = 'ASR_PhoWhisper' WHERE asr_model_id = 'ASR_LocalWhisper';
UPDATE ai_agent_template SET asr_model_id = 'ASR_PhoWhisper' WHERE asr_model_id = 'ASR_LocalWhisper';
UPDATE ai_model_config SET is_default = (id = 'ASR_PhoWhisper') WHERE model_type = 'ASR';
UPDATE ai_model_config SET is_enabled = 0 WHERE id = 'ASR_LocalWhisper';
SELECT agent_name, asr_model_id FROM ai_agent;
SELECT id, model_name, is_default, is_enabled FROM ai_model_config WHERE id IN ('ASR_LocalWhisper','ASR_PhoWhisper');
