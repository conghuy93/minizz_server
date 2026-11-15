-- Per-agent Gemini API keys (main + 3 backups), entered by each user (admin included) in
-- Agent > Chỉnh sửa chức năng > "Gemini API Key (của bạn)".
-- Server patches: connection.py (user-gemini-key) + openai.py (key-failover: 429/401/403/invalid key -> next key).
SET NAMES utf8mb4;
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_PLUGIN_USER_GEMINI_KEY';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_USER_GEMINI_KEY', 'Plugin', 'user_gemini_key', 'Gemini API Key (của bạn)',
        JSON_ARRAY(
          JSON_OBJECT('key','api_key',      'type','string','label','Gemini API key chính (aistudio.google.com/apikey)','default',''),
          JSON_OBJECT('key','backup_key_1', 'type','string','label','Key dự phòng 1 (dùng khi key chính hết hạn mức)','default',''),
          JSON_OBJECT('key','backup_key_2', 'type','string','label','Key dự phòng 2','default',''),
          JSON_OBJECT('key','backup_key_3', 'type','string','label','Key dự phòng 3','default','')),
        1, 0, NOW(), 0, NOW());

-- Admin works the same way: move the admin key from the shared model config into the admin's own agent (miniz)
DELETE FROM ai_agent_plugin_mapping WHERE agent_id = '6b189a1ec5d94eef8cb32720f1afee3e' AND plugin_id = 'SYSTEM_PLUGIN_USER_GEMINI_KEY';
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT '6b189a1ec5d94eef8cb32720f1afee3e', 'SYSTEM_PLUGIN_USER_GEMINI_KEY',
       JSON_OBJECT('api_key', JSON_UNQUOTE(JSON_EXTRACT(config_json, '$.api_key')),
                   'backup_key_1', '', 'backup_key_2', '', 'backup_key_3', '')
FROM ai_model_config WHERE id = 'LLM_GeminiOpenAI' AND JSON_UNQUOTE(JSON_EXTRACT(config_json, '$.api_key')) <> '';

-- No shared key any more: an agent without its own key cannot use Gemini
UPDATE ai_model_config SET config_json = JSON_SET(config_json, '$.api_key', '') WHERE id IN ('LLM_GeminiOpenAI', 'VLLM_GeminiVLLM');

SELECT a.agent_name, m.plugin_id, CONCAT('…', RIGHT(JSON_UNQUOTE(JSON_EXTRACT(m.param_info,'$.api_key')),4)) AS key_tail
FROM ai_agent a JOIN ai_agent_plugin_mapping m ON m.agent_id = a.id WHERE m.plugin_id = 'SYSTEM_PLUGIN_USER_GEMINI_KEY';
SELECT id, JSON_EXTRACT(config_json, '$.api_key') AS shared_key FROM ai_model_config WHERE id IN ('LLM_GeminiOpenAI','VLLM_GeminiVLLM');
