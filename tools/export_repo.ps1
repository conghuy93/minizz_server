# Gom ma nguon + cau hinh (khong co du lieu, model, secret) vao F:\minizz_server e ay len GitHub
$ErrorActionPreference = "Stop"
$S = "F:\xiaozhi-server"; $D = "F:\minizz_server"
if (-not (Test-Path $D)) { New-Item -ItemType Directory $D | Out-Null }
# xoa moi thu tru .git
Get-ChildItem $D -Force | Where-Object Name -ne ".git" | Remove-Item -Recurse -Force

function C($src, $dst) {
    $full = Join-Path $D $dst
    New-Item -ItemType Directory -Force (Split-Path $full) | Out-Null
    Copy-Item $src $full -Force
}

C "$S\docker-compose_all.yml"            "docker-compose_all.yml"
C "$S\HUONG_DAN_XAY_DUNG_SERVER.md"      "HUONG_DAN_XAY_DUNG_SERVER.md"
Get-ChildItem "$S\patch\*.py"            | % { C $_.FullName "patch\$($_.Name)" }
C "$S\google-auth\app.py"                "google-auth\app.py"
C "$S\google-auth\Dockerfile"            "google-auth\Dockerfile"
foreach ($f in "app.py", "Dockerfile", "selftest.py", "asrtest.py") { C "$S\tts-router\$f" "tts-router\$f" }
C "$S\voicevox\make_voicevox.py"         "voicevox\make_voicevox.py"
Get-ChildItem "$S\tools\*" -File         | % { C $_.FullName "tools\$($_.Name)" }
foreach ($f in "setup_vn_local", "add_phowhisper", "use_phowhisper", "add_user_gemini_key", "viet_hoa", "viet_hoa_templates",
               "enable_memory", "voiceprint_db", "enable_voiceprint", "public_urls", "add_template_mysoi", "use_tts_router",
               "voicevox", "template_mysoi_ja", "template_mysoi_ja_v2") { C "$S\sql\$f.sql" "sql\$f.sql" }
Get-ChildItem "$S\voice-demo\*" -File -Include *.py, *.sql | % { C $_.FullName "voice-demo\$($_.Name)" }
C "$S\voiceprint\voiceprint_service.py"  "voiceprint\voiceprint_service.py"
C "$S\cloudflared\config.yml"            "cloudflared\config.yml"
C "F:\whisper-asr\server.py"             "asr\server.py"
C "F:\whisper-asr\start_phowhisper_gpu.bat" "asr\start_phowhisper_gpu.bat"
C "F:\VieNeu-TTS\start_api_gpu.bat"      "vieneu\start_api_gpu.bat"
C "$S\manager-web-build\apply_vi.py"     "web\apply_vi.py"
C "$S\manager-web-build\vi_map.json"     "web\vi_map.json"
$W = "$S\manager-web-build\main\manager-web"
foreach ($f in "src\components\AddWisdomBodyDialog.vue", "src\views\login.vue", "src\views\register.vue", "src\views\auth.scss",
               "src\utils\subscription.js", "src\views\UserManagement.vue", "src\components\HeaderBar.vue",
               "src\views\roleConfig.vue") { C "$W\$f" "web\manager-web\$f" }
"Da gom: " + (Get-ChildItem $D -Recurse -File | Where-Object FullName -notlike "*\.git\*").Count + " file"

# ---- Che secret / thong tin rieng (chay lai script luc nao cung an toan) ----
function Scrub($rel, $pattern, $repl) {
    $p = Join-Path $D $rel
    $t = [IO.File]::ReadAllText($p)
    $n = [regex]::Replace($t, $pattern, $repl)
    [IO.File]::WriteAllText($p, $n, (New-Object Text.UTF8Encoding $false))
}
Scrub "sql\setup_vn_local.sql"   "AQ\.[A-Za-z0-9_\-]{20,}|AIza[0-9A-Za-z_\-]{20,}" "<GEMINI_API_KEY>"
Scrub "sql\setup_vn_local.sql"   "192\.168\.\d+\.\d+" "<LAN_IP>"
Scrub "sql\enable_voiceprint.sql" "key=[0-9a-f\-]{36}" "key=<VOICEPRINT_KEY>"
Scrub "cloudflared\config.yml"   "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" "<TUNNEL_ID>"
Scrub "HUONG_DAN_XAY_DUNG_SERVER.md" "192\.168\.\d+\.\d+" "<LAN_IP>"
Scrub "tools\xiaozhi.ps1"        "192\.168\.\d+\.\d+" "<LAN_IP>"

# ---- File mau ----
$U = New-Object Text.UTF8Encoding $false
[IO.File]::WriteAllText("$D\google-auth\.env.example", @"
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
PUBLIC_BASE=https://<ten-mien-web>
GOOGLE_ALLOW_REGISTER=true
# DB_PASSWORD=<mat-khau-mysql>
"@, $U)
Copy-Item "$S\voiceprint\.voiceprint.yaml" "$D\voiceprint\.voiceprint.example.yaml" -Force
Scrub "voiceprint\.voiceprint.example.yaml" "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" "<VOICEPRINT_KEY>"
Scrub "voiceprint\.voiceprint.example.yaml" "(?im)^(\s*(password|passwd|secret)\s*:\s*).*$" '$1<SECRET>'
[IO.File]::WriteAllText("$D\cloudflared\credentials.example.json", @"
{"AccountTag":"<account-tag>","TunnelSecret":"<tunnel-secret>","TunnelID":"<TUNNEL_ID>"}
"@, $U)
Copy-Item "$D\HUONG_DAN_XAY_DUNG_SERVER.md" "$D\README.md" -Force
[IO.File]::WriteAllText("$D\.gitignore", @"
# secret - KHONG BAO GIO commit
.env
*.env
!*.env.example
cloudflared/credentials.json
voiceprint/.voiceprint.yaml
data/
mysql/
models/
uploadfile/
*.log
*.wav
*.mp3
*.tgz
node_modules/
dist/
__pycache__/
"@, $U)
"Da che secret + tao file mau"
