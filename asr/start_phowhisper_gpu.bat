@echo off
REM PhoWhisper (VinAI, Whisper fine-tuned for Vietnamese) - OpenAI-compatible ASR on port 8012.
REM Japanese: whisper-large-v3-turbo detects language; Japanese utterances use turbo, others PhoWhisper.
cd /d F:\whisper-asr
set HOST=0.0.0.0
set PORT=8012
set ASR_MODEL=vinai/PhoWhisper-medium
set ASR_LANGUAGE=vi
set ALT_MODEL=openai/whisper-large-v3-turbo
set ALT_LANGS=ja
set ASR_API_KEY=local-asr-key
set PYTHONIOENCODING=utf-8
F:\VieNeu-TTS\.venv\Scripts\python.exe server.py >> F:\whisper-asr\phowhisper.log 2>&1
