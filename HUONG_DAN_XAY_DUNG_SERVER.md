# Hướng dẫn xây dựng server xiaozhi cho robot miniZ

Tài liệu ghi lại toàn bộ cách dựng server **xiaozhi-esp32-server** tự host cho robot miniZ: LLM Gemini, TTS/ASR chạy local trên GPU, giao diện web tiếng Việt, đăng nhập Google, gói sử dụng, truy cập công khai qua Cloudflare, và chế độ song ngữ Việt – Nhật.

> ⚠️ Tài liệu **không chứa mật khẩu / API key / secret**. Các chỗ `<...>` là giá trị bạn tự điền. Secret thật nằm ở `google-auth\.env`, `cloudflared\credentials.json` và trong database – không chia sẻ các file này.

---

## 1. Tổng quan kiến trúc

```
Robot (ESP32-S3)
   │  WebSocket  wss://xiaozhi-ws.minizjp.com
   ▼
Cloudflare Tunnel (container xiaozhi-cloudflared)
   ├── xiaozhi.minizjp.com         → web (8002)  + /auth/* → xiaozhi-google-auth (8090)
   ├── xiaozhi-ws.minizjp.com      → xiaozhi-esp32-server (8000, WebSocket)
   └── xiaozhi-vision.minizjp.com  → xiaozhi-esp32-server (8003, vision/OTA)

xiaozhi-esp32-server (Python) ──► Gemini API (LLM, key theo từng người dùng)
        │
        ├── ASR: http://host.docker.internal:8012  (PhoWhisper + Whisper turbo, GPU, chạy ngoài Docker)
        ├── TTS: http://xiaozhi-tts-router:8020   (router Việt/Nhật)
        │          ├── VieNeu-TTS  host:8010 (GPU, ngoài Docker)  – tiếng Việt
        │          └── VOICEVOX    voicevox:50021 (CPU, Docker)   – tiếng Nhật
        ├── voiceprint-api (nhận diện người nói)
        └── manager-api (Java) + MySQL + Redis  ← web quản trị (Vue, đã Việt hoá)
```

**Máy chủ:** Windows, RTX 4070 12 GB, IP LAN `<LAN_IP>`. VRAM dùng ~9,3 GB (PhoWhisper-medium + Whisper turbo + VieNeu).

### Bảng cổng

| Dịch vụ | Cổng | Chạy ở | Ghi chú |
|---|---|---|---|
| xiaozhi-esp32-server | 8000 (WS), 8003 (HTTP) | Docker | |
| web (manager-web + manager-api) | 8002 | Docker | |
| xiaozhi-google-auth | 8090 | Docker | đăng nhập Google, gói sử dụng |
| xiaozhi-tts-router | 8020 | Docker | chỉ nội bộ |
| voicevox | 50021 | Docker | chỉ nội bộ |
| VieNeu-TTS | 8010 | Windows (GPU) | key `vieneu-local-key` |
| PhoWhisper ASR | 8012 | Windows (GPU) | key `local-asr-key` |
| MySQL / Redis | — | Docker | |

---

## 2. Cấu trúc thư mục `F:\xiaozhi-server`

```
docker-compose_all.yml        # toàn bộ stack
data\                         # .config.yaml của server python
patch\                        # file python đã sửa, mount đè (read-only) vào image
   connection.py              # thought_signature, key người dùng, chế độ tiếng Nhật
   openai.py                  # fix Gemini thought_signature + tự đổi key dự phòng
   mem_local_short.py         # bộ nhớ dài hạn tiếng Việt, theo từng người nói
   receiveAudioHandle.py      # chặn robot khi hết hạn gói
google-auth\                  # app.py + Dockerfile + .env (Google OAuth, gói sử dụng)
tts-router\                   # app.py + Dockerfile (router Việt/Nhật, chuẩn hoá âm lượng)
voicevox\make_voicevox.py     # tạo danh sách giọng VOICEVOX + file nghe thử
voiceprint\                   # cấu hình + bản vá voiceprint-api
cloudflared\                  # config.yml + credentials.json của tunnel
web-vi\                       # bản build web tiếng Việt (nginx phục vụ)
web-vi\voice-demo\            # mp3 nghe thử giọng (VieNeu + VOICEVOX)
manager-web-build\            # mã nguồn web để build lại + apply_vi.py, vi_map.json
sql\                          # các file SQL cấu hình
```

Ngoài Docker:
- `F:\VieNeu-TTS\start_api_gpu.bat` – TTS tiếng Việt (cổng 8010)
- `F:\whisper-asr\server.py`, `start_phowhisper_gpu.bat` – ASR (cổng 8012)

---

## 3. Cài đặt từng bước

### 3.1. Chuẩn bị
1. Windows + driver NVIDIA mới, Docker Desktop (WSL2), Git, Node.js (để build web), ffmpeg.
2. Clone `https://github.com/xinnan-tech/xiaozhi-esp32-server` và dựng **chế độ full** (server + manager-api + web + MySQL + Redis) theo tài liệu gốc, đặt ở `F:\xiaozhi-server`.
3. Lệnh dùng chung cho mọi thao tác compose:
   ```powershell
   cd F:\xiaozhi-server
   docker compose -p xiaozhi-server -f docker-compose_all.yml up -d
   ```

### 3.2. TTS tiếng Việt – VieNeu-TTS v3 Turbo (GPU)
- Cài VieNeu-TTS vào `F:\VieNeu-TTS` (venv `.venv`).
- `start_api_gpu.bat` chạy API kiểu OpenAI `/v1/audio/speech` ở cổng **8010**, đặt `VIENEU_API_KEY=vieneu-local-key`.
- Có 25 giọng mẫu (Hải Đăng, Mai Anh, Ngọc Huyền…). Hỗ trợ trả PCM và tham số `sample_rate`.

### 3.3. ASR – PhoWhisper + Whisper turbo (GPU)
`F:\whisper-asr\start_phowhisper_gpu.bat` (**chỉ dùng ký tự ASCII trong file .bat**, chữ có dấu làm cmd đọc sai biến):
```bat
set PORT=8012
set ASR_MODEL=vinai/PhoWhisper-medium
set ASR_LANGUAGE=vi
set ALT_MODEL=openai/whisper-large-v3-turbo
set ALT_LANGS=ja
set ASR_API_KEY=local-asr-key
F:\VieNeu-TTS\.venv\Scripts\python.exe server.py >> F:\whisper-asr\phowhisper.log 2>&1
```
`server.py` làm gì:
- Whisper turbo tính **xác suất ngôn ngữ** của từng câu.
- Chế độ thường (tiếng Việt): câu tiếng Nhật → Whisper turbo, còn lại → PhoWhisper.
- Chế độ Nhật (server gửi `model` có đuôi `|ja`): mặc định Whisper turbo tiếng Nhật; chỉ dùng PhoWhisper khi xác suất tiếng Việt ≥ `JA_MODE_VI_CONF` (mặc định 0.8).
- Cổng lọc im lặng (`ASR_MIN_DBFS=-50`) và bộ lọc câu "ảo giác" của Whisper (vd "Ghiền Mì Gõ", "ご視聴ありがとうございました").
- Log ở `F:\whisper-asr\phowhisper.log` (dòng `mode=… language=… -> alt/main`).

Khởi động lại ASR:
```powershell
$p=(Get-NetTCPConnection -LocalPort 8012 -State Listen).OwningProcess | Select -Unique
$p | % { Stop-Process -Id $_ -Force }
Start-Process F:\whisper-asr\start_phowhisper_gpu.bat -WindowStyle Minimized
```

### 3.4. TTS tiếng Nhật – VOICEVOX + TTS router
Thêm vào `docker-compose_all.yml`:
```yaml
  voicevox:
    image: voicevox/voicevox_engine:cpu-latest
    container_name: voicevox
    restart: always

  xiaozhi-tts-router:
    build: ./tts-router
    image: xiaozhi-tts-router:local
    container_name: xiaozhi-tts-router
    restart: always
    depends_on: [voicevox]
    extra_hosts: ["host.docker.internal:host-gateway"]
    environment:
      - JA_SPEAKER=3        # giọng Nhật mặc định ở chế độ Việt (ずんだもん)
      # - VI_VOICE=Mai Anh  # giọng Việt dùng trong chế độ Nhật
      # - TARGET_DBFS=-18   # độ to chuẩn hoá
```
Router (`tts-router\app.py`, API giống OpenAI `/v1/audio/speech`, Bearer `vieneu-local-key`):
- **Model khác `voicevox`** (chế độ Việt): `voice` = giọng VieNeu; đoạn chữ Nhật đọc bằng VOICEVOX (`JA_SPEAKER`, hoặc voice dạng `Mai Anh|ja=3`).
- **Model `voicevox`** (chế độ Nhật): `voice` = id giọng VOICEVOX (`3` hoặc `3|vi=Mai Anh`); chỉ đoạn có chữ tiếng Việt có dấu mới đọc bằng VieNeu, chữ Latin khác (OK, AI) vẫn VOICEVOX.
- Ghép các đoạn thành WAV 24 kHz, **chuẩn hoá âm lượng** mọi đoạn về `TARGET_DBFS` (VOICEVOX vốn nhỏ hơn VieNeu ~5 dB) và chặn đỉnh mềm.
- `/health`, `/voicevox/speakers` để kiểm tra.

> Lưu ý: sau khi chép file vào `tts-router\` hãy kiểm tra file đã được ghi xong trước khi `--build`, nếu không image sẽ dùng code cũ.

Cập nhật và build:
```powershell
docker compose -p xiaozhi-server -f docker-compose_all.yml up -d --build voicevox xiaozhi-tts-router
```

### 3.5. Cấu hình model trong database
Database: `xiaozhi_esp32_server`. **Luôn nạp SQL qua `cmd` để giữ UTF-8** (PowerShell pipe làm hỏng chữ có dấu/chữ Nhật):
```powershell
cmd /c "docker exec -i xiaozhi-esp32-server-db mysql -uroot -p<mật_khẩu_mysql> --default-character-set=utf8mb4 xiaozhi_esp32_server < sql\<file>.sql"
docker exec xiaozhi-esp32-server-redis redis-cli FLUSHALL   # BẮT BUỘC sau mỗi lần sửa DB
docker restart xiaozhi-esp32-server
```
Các bảng quan trọng: `ai_model_config`, `ai_model_provider`, `ai_agent_template` (module mặc định khi tạo agent), `ai_agent`, `ai_tts_voice` (có cột `voice_demo`), `sys_params`, `sys_user`, `sys_user_token`, `ai_device`, `user_subscription`.

Các file SQL đã dùng (thư mục `sql\`), theo thứ tự:

| File | Nội dung |
|---|---|
| `setup_vn_local.sql` | Gemini LLM + VieNeu TTS + Whisper |
| `add_phowhisper.sql`, `use_phowhisper.sql` | thêm ASR PhoWhisper, đặt làm mặc định |
| `add_user_gemini_key.sql` | ô nhập Gemini key + 3 key dự phòng trên web |
| `viet_hoa.sql`, `viet_hoa_templates.sql` | Việt hoá tên model, mẫu vai trò |
| `enable_memory.sql` | bật bộ nhớ dài hạn |
| `voiceprint_db.sql`, `enable_voiceprint.sql` | nhận diện người nói |
| `public_urls.sql` | URL công khai (OTA, WebSocket, vision) |
| `add_template_mysoi.sql` | mẫu "My Sói" |
| `voice_demo.sql` | link nghe thử 25 giọng VieNeu |
| `use_tts_router.sql` | TTS VieNeu trỏ sang router `http://xiaozhi-tts-router:8020/v1/audio/speech` |
| `voicevox.sql` | model `TTS_VoiceVox` + 51 giọng Nhật (sinh bởi `make_voicevox.py`) |
| `template_mysoi_ja.sql`, `template_mysoi_ja_v2.sql` | mẫu "My Sói (Tiếng Nhật)" |

Model chính đang dùng:
- **LLM:** Gemini qua endpoint OpenAI-compatible `https://generativelanguage.googleapis.com/v1beta/openai/`, model `gemini-3.5-flash-lite`.
- **ASR:** `ASR_PhoWhisper` → `http://host.docker.internal:8012/v1/audio/transcriptions`.
- **TTS:** `TTS_VieNeuTTS` (Việt) và `TTS_VoiceVox` (Nhật, `model=voicevox`), cả hai qua router.

### 3.6. Các bản vá server Python (`patch\`)
Mount đè trong compose (service `xiaozhi-esp32-server`):
```yaml
volumes:
  - ./data:/opt/xiaozhi-esp32-server/data
  - ./patch/connection.py:/opt/xiaozhi-esp32-server/core/connection.py:ro
  - ./patch/openai.py:/opt/xiaozhi-esp32-server/core/providers/llm/openai/openai.py:ro
  - ./patch/mem_local_short.py:/opt/xiaozhi-esp32-server/core/providers/memory/mem_local_short/mem_local_short.py:ro
  - ./patch/receiveAudioHandle.py:/opt/xiaozhi-esp32-server/core/handle/receiveAudioHandle.py:ro
```
(Đường dẫn trong container kiểm tra lại theo phiên bản image.)

| Bản vá | Mục đích |
|---|---|
| Gemini `thought_signature` | Gemini báo lỗi 400 khi gọi tool nếu thiếu chữ ký. Giữ `extra_content` khi gộp tool call; thiếu thì chèn `skip_thought_signature_validator`. |
| Key theo người dùng | `_apply_user_gemini_key` đọc plugin `user_gemini_key` (api_key + backup_key_1..3) và gán cho mọi LLM/SLM/VLLM có `googleapis.com`. |
| Tự đổi key | `_create_with_failover`: lỗi 401/403/429 hoặc 400 liên quan API key → chuyển key kế tiếp. |
| Bộ nhớ tiếng Việt | Tóm tắt bằng tiếng Việt, tách theo `[Người nói: X]`, ghi thẳng vào `ai_agent.summary_memory`; bỏ qua kết quả rỗng/"(trống)". |
| Gói sử dụng | Kiểm tra `user_subscription` sau bước bind; hết hạn → robot nói thông báo rồi đóng kết nối. |
| Chế độ tiếng Nhật | `_apply_language_mode`: nếu TTS đang chọn có `model=voicevox` → thêm `|ja` vào model ASR và chèn quy tắc "luôn trả lời tiếng Nhật, chỉ nói tiếng Việt khi được yêu cầu dịch/giải thích" vào đầu prompt. |

### 3.7. Nhận diện người nói (voiceprint-api)
- Service `voiceprint-api` mount `./voiceprint`, `./voiceprint/modelscope-cache`, `./voiceprint/voiceprint_service.py`.
- Lỗi ModelScope "download incomplete" → tải tay `configuration.json` và vá service để nạp model từ đường dẫn local.
- Dùng đúng key do service tự sinh trong `voiceprint\.voiceprint.yaml`.
- Điểm tham khảo: giọng đã đăng ký ~0,75; người lạ ~0,30.

### 3.8. Web quản trị tiếng Việt
Mã nguồn: `F:\xiaozhi-server\manager-web-build\main\manager-web`. Build lại:
```powershell
cd F:\xiaozhi-server\manager-web-build\main\manager-web
npm ci          # lần đầu
npm run build
cd ..\..
python apply_vi.py           # dịch 68 chuỗi tiếng Trung còn sót (vi_map.json)
# sao lưu bản cũ rồi chép dist sang web-vi
Remove-Item -Recurse ..\web-vi-prev -ErrorAction SilentlyContinue
Rename-Item ..\web-vi web-vi-prev
Copy-Item -Recurse main\manager-web\dist ..\web-vi
```
Service `web` mount `./web-vi:/usr/share/nginx/html:ro`. Sau khi cập nhật, người dùng cần **Ctrl+F5**.

Những phần đã sửa trong mã web:
- `AddWisdomBodyDialog.vue` – "Thêm tác nhân" chỉ cần nhập **mã 6 số** của robot (tạo agent "Robot {mã}" rồi bind; bind lỗi thì xoá agent).
- `login.vue`, `register.vue`, `auth.scss` – nút Google, ô "Ghi nhớ đăng nhập (30 ngày)".
- `UserManagement.vue` – cột "Hạn sử dụng" + menu "Cấp quyền".
- `HeaderBar.vue` – huy hiệu hạn sử dụng.
- `roleConfig.vue` – prompt tối đa 8000 ký tự, bộ nhớ 4000; nút nghe thử giọng.
- `public\voice-demo\*.mp3` – file nghe thử.

### 3.9. Đăng nhập Google + gói sử dụng (`google-auth\`)
1. Google Cloud Console → tạo OAuth Client (Web), Authorized redirect URI: `https://xiaozhi.minizjp.com/auth/google/callback`. Điền Branding và **Publish app** (In production), nếu không người ngoài không đăng nhập được.
2. `google-auth\.env`:
   ```
   GOOGLE_CLIENT_ID=<client id>
   GOOGLE_CLIENT_SECRET=<client secret>
   PUBLIC_BASE=https://xiaozhi.minizjp.com
   GOOGLE_ALLOW_REGISTER=true
   ```
3. Endpoint:
   - `/auth/google/login?remember=1|0` → `/auth/google/callback` (tạo/tìm `sys_user`, tạo token 30 ngày hoặc 12 giờ, chuyển về `/#/login?gtoken=…`).
   - `/auth/me/subscription`, `/auth/admin/subscriptions?ids=`.
   - `POST /auth/admin/subscriptions/extend {userid, months: 0|1|3|6|12}` – cộng dồn thời hạn; `0` = thu hồi (đặt hết hạn = hiện tại − 1 phút).
   - `POST /auth/remember` – kéo dài token hiện tại lên 30 ngày (đăng nhập bằng mật khẩu).
4. Quy tắc: chỉ cho **đăng ký bằng Google**; tài khoản mới dùng thử **3 ngày**; admin không giới hạn.

### 3.10. Cloudflare Tunnel (truy cập từ ngoài)
`cloudflared\config.yml`:
```yaml
tunnel: <tunnel-id>
credentials-file: /etc/cloudflared/credentials.json
ingress:
  - hostname: xiaozhi.minizjp.com
    path: ^/auth/
    service: http://xiaozhi-google-auth:8090
  - hostname: xiaozhi.minizjp.com
    service: http://xiaozhi-esp32-server-web:8002
  - hostname: xiaozhi-ws.minizjp.com
    service: http://xiaozhi-esp32-server:8000
  - hostname: xiaozhi-vision.minizjp.com
    service: http://xiaozhi-esp32-server:8003
  - service: http_status:404
```
Container chạy `tunnel --no-autoupdate --protocol http2 --config /etc/cloudflared/config.yml run` (http2 ổn định hơn QUIC trên mạng nhà). Cập nhật URL công khai trong `sys_params` (`sql\public_urls.sql`).

---

## 4. Sử dụng

### Người dùng
1. Vào `https://xiaozhi.minizjp.com` → **Đăng nhập bằng Google**.
2. Bật robot, robot đọc mã 6 số → **Thêm tác nhân** → nhập mã.
3. **Cấu hình vai trò**: chọn mẫu (vd My Sói / My Sói (Tiếng Nhật)), chọn giọng (bấm ▶ nghe thử).
4. **Chỉnh sửa chức năng → Gemini API Key**: nhập key chính + tối đa 3 key dự phòng.
5. Lưu, khởi động lại robot.

### Song ngữ Việt – Nhật
- **Chế độ Việt** (TTS VieNeu): nói tiếng Việt; câu tiếng Nhật vẫn được nhận dạng và đọc bằng VOICEVOX.
- **Chế độ Nhật** (TTS "VOICEVOX (Tiếng Nhật, local)", 51 giọng): ưu tiên nghe tiếng Nhật, luôn trả lời tiếng Nhật, chỉ nói tiếng Việt khi được yêu cầu dịch/giải thích.
- Bản quyền VOICEVOX: mỗi nhân vật có điều khoản riêng, đa số yêu cầu **ghi tên "VOICEVOX:<tên nhân vật>"** khi dùng; đọc điều khoản trước khi dùng thương mại.

### Admin
- **Quản lý người dùng → Cấp quyền**: 1 / 3 / 6 tháng, 1 năm, hoặc thu hồi.

---

## 5. Vận hành & sửa lỗi

### Lệnh hay dùng
```powershell
# xem log
docker logs xiaozhi-esp32-server --tail 100
docker logs xiaozhi-tts-router --tail 50
Get-Content F:\whisper-asr\phowhisper.log -Tail 30 -Encoding utf8

# GPU
nvidia-smi --query-gpu=memory.used --format=csv

# kiểm tra dịch vụ
Invoke-RestMethod http://127.0.0.1:8012/health
docker exec xiaozhi-tts-router python -c "import httpx;print(httpx.get('http://localhost:8020/health').text)"
```

### Đặt lại mật khẩu admin
Mật khẩu lưu dạng BCrypt (`$2a$10$…`). Tạo hash mới (vd Python `bcrypt.hashpw(pw, bcrypt.gensalt(10, prefix=b"2a"))`), rồi:
```sql
UPDATE sys_user SET password='<hash>' WHERE username='admin' AND super_admin=1;
DELETE FROM sys_user_token WHERE user_id=<id admin>;
```
Flush Redis, đăng nhập và đổi mật khẩu ngay.

### Lỗi thường gặp

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| Gemini 400 "missing thought_signature" | Thiếu bản vá `connection.py` / `openai.py`. |
| Robot nói "主人，小智现在有点忙" | LLM lỗi (key sai/hết hạn mức) – xem log server, kiểm tra key người dùng. |
| ASR ra "Ghiền Mì Gõ" | Whisper bịa khi im lặng → bộ lọc ảo giác + PhoWhisper. |
| Sửa model mà server vẫn dùng model cũ | `ai_agent_template`/`ai_agent` quyết định module; sửa DB rồi **FLUSHALL Redis**. |
| Bộ nhớ tóm tắt bằng tiếng Trung | Cần bản vá `mem_local_short.py`. |
| Tên/giọng hiện "????" sau khi nạp SQL | Nạp qua PowerShell pipe → dùng `cmd /c "... < file.sql"`. |
| Biến trong .bat không có tác dụng | File .bat có chữ có dấu → chỉ dùng ASCII. |
| Đăng nhập Google: redirect_uri_mismatch | Sửa redirect URI trong Console cho khớp. |
| Người ngoài không đăng nhập Google được | App OAuth đang "Testing" → Publish. |
| Web vẫn hiện bản cũ | Ctrl+F5 (cache app.js). |
| File nghe thử không phát | Phục vụ mp3 (wav bị trả về octet-stream). |
| Giọng Nhật nhỏ hơn giọng Việt | Router chuẩn hoá âm lượng (`TARGET_DBFS`). |
| Robot đọc mã bind bằng tiếng Trung | Chưa Việt hoá câu bind (việc còn tồn). |

### Việc còn tồn
- Mẫu My Sói nhắc tới các tool (`self.minizdog.*`, `self.emotion`, thời tiết, vòng quay, cung hoàng đạo, báo thức…) mà firmware miniZ_ninja 2.2.2.17 chưa có.
- Câu đọc mã bind vẫn là tiếng Trung.
