-- Mẫu My Sói (Tiếng Nhật): quy tắc ngôn ngữ do server tự thêm khi TTS = VOICEVOX (patch ja-mode), nên prompt = My Sói gốc
UPDATE ai_agent_template t JOIN ai_agent_template s ON s.id = 'b7c3e1f0a9d24c6e8f1a2b3c4d5e6f70'
SET t.system_prompt = s.system_prompt
WHERE t.id = 'c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81';
SELECT agent_name, LEFT(system_prompt, 40) FROM ai_agent_template WHERE id = 'c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81';
