-- B?t nh?n di?n ng??i n?i: t?nh n?ng web + ??a ch? voiceprint-api + l?u ?m thanh h?i tho?i ?? ??ng k? gi?ng
SET NAMES utf8mb4;
UPDATE sys_params SET param_value = JSON_SET(param_value, '$.features.voiceprintRecognition.enabled', true)
 WHERE param_code = 'system-web.menu';
UPDATE sys_params SET param_value = 'http://voiceprint-api:8005/voiceprint/health?key=<VOICEPRINT_KEY>'
 WHERE param_code = 'server.voice_print';
-- 2 = b?o c?o c? ch? + ?m thanh (c?n ?? ch?n ?o?n ghi ?m khi ??ng k? gi?ng)
UPDATE ai_agent SET chat_history_conf = 2 WHERE id = '6b189a1ec5d94eef8cb32720f1afee3e';
UPDATE ai_agent_template SET chat_history_conf = 2;
SELECT JSON_EXTRACT(param_value, '$.features.voiceprintRecognition.enabled') AS voiceprint_on FROM sys_params WHERE param_code = 'system-web.menu';
SELECT param_value FROM sys_params WHERE param_code = 'server.voice_print';
SELECT agent_name, chat_history_conf FROM ai_agent;

