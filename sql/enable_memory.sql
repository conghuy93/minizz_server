-- Long-term memory (Bộ nhớ local, LLM tóm tắt) using the agent's own Gemini (patch vn-memory)
SET NAMES utf8mb4;
UPDATE ai_model_config SET config_json = JSON_OBJECT('type','mem_local_short','llm','LLM_GeminiOpenAI'),
       model_name = 'Bộ nhớ dài hạn (Gemini tóm tắt, tiếng Việt)' WHERE id = 'Memory_mem_local_short';
UPDATE ai_model_config SET is_default = (id = 'Memory_mem_local_short') WHERE model_type = 'Memory';
UPDATE ai_agent_template SET mem_model_id = 'Memory_mem_local_short';
UPDATE ai_agent SET mem_model_id = 'Memory_mem_local_short' WHERE id = '6b189a1ec5d94eef8cb32720f1afee3e';
SELECT agent_name, mem_model_id FROM ai_agent;
