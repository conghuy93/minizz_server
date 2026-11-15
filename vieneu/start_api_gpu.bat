@echo off
REM VieNeu-TTS OpenAI-compatible API on GPU, for xiaozhi-server (Docker reaches it via host.docker.internal:8010)
REM Port 8010 because xiaozhi-server uses 8000.
cd /d F:\VieNeu-TTS
set HOST=0.0.0.0
set PORT=8010
set VIENEU_DEVICE=cuda
set VIENEU_MAX_STREAMS=16
set VIENEU_API_KEY=vieneu-local-key
"C:\Users\congh\AppData\Roaming\Python\Python313\Scripts\uv.exe" run python -m apps.openai_speech >> F:\VieNeu-TTS\api.log 2>&1
