-- Mẫu "My Sói (Tiếng Nhật)": nói tiếng Nhật là chính, vẫn trả lời tiếng Việt khi được hỏi bằng tiếng Việt
DELETE FROM ai_agent_template WHERE id='c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81';
INSERT INTO ai_agent_template (id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id, vllm_model_id,
  tts_model_id, tts_voice_id, tts_language, tts_volume, tts_rate, tts_pitch, mem_model_id, intent_model_id,
  system_prompt, summary_memory, chat_history_conf, lang_code, language, sort, creator, created_at)
SELECT 'c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81', agent_code, 'My Sói (Tiếng Nhật)', asr_model_id, vad_model_id, llm_model_id, vllm_model_id,
  'TTS_VoiceVox', 'TTS_VV_003', tts_language, tts_volume, tts_rate, tts_pitch, mem_model_id, intent_model_id,
  CONCAT('NGÔN NGỮ (ưu tiên cao nhất, đè lên mọi quy tắc bên dưới):\n',
    '- Mặc định nói TIẾNG NHẬT tự nhiên, văn nói, câu ngắn. Viết bằng chữ Nhật (kana/kanji), KHÔNG viết romaji, không kèm phiên âm.\n',
    '- Nếu người dùng nói tiếng Việt hoặc yêu cầu tiếng Việt thì trả lời bằng TIẾNG VIỆT. Khi người dùng quay lại tiếng Nhật thì trả lời tiếng Nhật.\n',
    '- Khi dạy/giải thích tiếng Nhật bằng tiếng Việt: câu nói bằng tiếng Việt, còn từ tiếng Nhật viết bằng chữ Nhật (vd: Con chó là 犬 nhé).\n',
    '- Không trộn hai thứ tiếng trong một câu nếu không cần thiết.\n',
    '- Cách xưng hô tao–mày và các câu chửi bên dưới là khi nói tiếng Việt; khi nói tiếng Nhật dùng giọng suồng sã tương đương (俺/お前, ご主人), cà khịa kiểu Nhật (バカ, アホか, うるさい...).\n\n',
    system_prompt),
  summary_memory, chat_history_conf, 'ja', '日本語', 1, creator, NOW()
FROM ai_agent_template WHERE id='b7c3e1f0a9d24c6e8f1a2b3c4d5e6f70';
UPDATE ai_agent_template SET sort = sort + 1 WHERE sort >= 1 AND id <> 'c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81';
SELECT agent_name, tts_model_id, tts_voice_id, sort, CHAR_LENGTH(system_prompt) FROM ai_agent_template ORDER BY sort;
UPDATE ai_agent_template SET tts_language='Tiếng Nhật' WHERE id='c8d4f2a1b0e35d7f9a2b3c4d5e6f7a81';
