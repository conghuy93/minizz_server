# Quản lý nhanh toàn bộ server xiaozhi (Docker + VieNeu-TTS + ASR)
# Cách dùng:  xiaozhi.ps1 start | stop | restart | status
param([ValidateSet("start", "stop", "restart", "status")][string]$Action = "start")

$ErrorActionPreference = "SilentlyContinue"
$Root    = "F:\xiaozhi-server"
$Compose = @("compose", "-p", "xiaozhi-server", "-f", "$Root\docker-compose_all.yml")
$DockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$VieNeuBat = "F:\VieNeu-TTS\start_api_gpu.bat"
$AsrBat    = "F:\whisper-asr\start_phowhisper_gpu.bat"

function Say($msg, $color = "Gray") { Write-Host $msg -ForegroundColor $color }

function Test-Http($url) {
    try { Invoke-RestMethod $url -TimeoutSec 3 | Out-Null; return $true } catch { return $false }
}
function Test-Text($url, $text) {
    try { return ((Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 4).Content -like "*$text*") } catch { return $false }
}
function Test-DbHealthy { (docker inspect -f "{{.State.Health.Status}}" xiaozhi-esp32-server-db) -eq "healthy" }
# Kiểm tra THẬT (cổng mở chưa đủ: docker luôn giữ cổng mở dù chương trình bên trong chưa chạy)
$ApiOk    = { Test-Http "http://127.0.0.1:8002/xiaozhi/user/pub-config" }
$ServerOk = { Test-Text "http://127.0.0.1:8000/xiaozhi/v1/" "Server is running" }
function Test-Port($port) {
    $c = New-Object Net.Sockets.TcpClient
    try { $c.ConnectAsync("127.0.0.1", $port).Wait(1500) -and $c.Connected } catch { $false } finally { $c.Close() }
}
function Test-Docker { docker info *> $null; return ($LASTEXITCODE -eq 0) }
function Stop-Port($port) {
    (Get-NetTCPConnection -LocalPort $port -State Listen).OwningProcess | Select-Object -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force }
}
function Wait-Until($name, [scriptblock]$check, $timeoutSec) {
    $t = 0
    while (-not (& $check)) {
        if ($t -ge $timeoutSec) { Say "  [X] $name chưa sẵn sàng sau $timeoutSec giây" Red; return $false }
        Start-Sleep 3; $t += 3
    }
    Say "  [OK] $name ($t giây)" Green; return $true
}

# Danh sách kiểm tra trạng thái
$Checks = [ordered]@{
    "Docker"                       = { Test-Docker }
    "VieNeu-TTS (8010, GPU)"       = { Test-Http "http://127.0.0.1:8010/health" }
    "ASR PhoWhisper (8012, GPU)"   = { Test-Http "http://127.0.0.1:8012/health" }
    "Cơ sở dữ liệu MySQL"          = { Test-DbHealthy }
    "API quản trị + OTA (8002)"    = { (& $ApiOk) -and (Test-Text "http://127.0.0.1:8002/xiaozhi/ota/" "OTA") }
    "xiaozhi server (8000 WS)"     = { & $ServerOk }
    "Google auth (8090)"           = { (docker inspect -f "{{.State.Running}}" xiaozhi-google-auth) -eq "true" }
    "TTS router + VOICEVOX"        = { (docker exec xiaozhi-tts-router python -c "import httpx;print(httpx.get('http://localhost:8020/health',timeout=5).json()['ok'])") -eq "True" }
    "Nhận diện giọng (voiceprint)" = { (docker inspect -f "{{.State.Running}}" voiceprint-api) -eq "true" }
    "Cloudflare tunnel"            = { (docker inspect -f "{{.State.Running}}" xiaozhi-cloudflared) -eq "true" }
}

function Show-Status {
    Say "`n===== TRẠNG THÁI SERVER XIAOZHI =====" Cyan
    $allOk = $true
    foreach ($k in $Checks.Keys) {
        $ok = & $Checks[$k]
        if (-not $ok) { $allOk = $false }
        Say ("  {0,-32} {1}" -f $k, $(if ($ok) { "CHẠY" } else { "TẮT / LỖI" })) $(if ($ok) { "Green" } else { "Red" })
    }
    $vram = nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
    if ($vram) { Say "  GPU VRAM: $vram" }
    Say "`n  Web:   https://xiaozhi.minizjp.com   (LAN: http://<LAN_IP>:8002)"
    Say "  Robot: wss://xiaozhi-ws.minizjp.com/xiaozhi/v1/"
    if ($allOk) { Say "`n  >>> TẤT CẢ ĐÃ SẴN SÀNG <<<" Green } else { Say "`n  >>> CÓ DỊCH VỤ CHƯA CHẠY - xem dòng màu đỏ <<<" Yellow }
}

function Start-All {
    $t0 = Get-Date
    Say "===== KHỞI ĐỘNG SERVER XIAOZHI (đầy đủ tính năng) =====" Cyan

    # 1) Docker Desktop
    if (-not (Test-Docker)) {
        Say "- Mở Docker Desktop..."
        Start-Process $DockerDesktop
    }

    # 2) Dịch vụ GPU chạy song song trong lúc chờ Docker (tiết kiệm thời gian)
    if (-not (Test-Http "http://127.0.0.1:8010/health")) {
        Say "- Bật VieNeu-TTS (GPU)..."
        Start-Process -FilePath $VieNeuBat -WindowStyle Minimized
    }
    if (-not (Test-Http "http://127.0.0.1:8012/health")) {
        Say "- Bật ASR PhoWhisper + Whisper turbo (GPU)..."
        Start-Process -FilePath $AsrBat -WindowStyle Minimized
    }

    # 3) Container
    if (-not (Wait-Until "Docker" { Test-Docker } 180)) { return }
    Say "- Bật các container (server, web, DB, Redis, Google auth, TTS router, VOICEVOX, voiceprint, Cloudflare)..."
    docker @Compose up -d 2>&1 | Out-Null

    # 4) Chờ sẵn sàng
    Say "- Chờ dịch vụ sẵn sàng..."
    Wait-Until "VieNeu-TTS"     { Test-Http "http://127.0.0.1:8010/health" } 240 | Out-Null
    Wait-Until "ASR PhoWhisper" { Test-Http "http://127.0.0.1:8012/health" } 240 | Out-Null
    Wait-Until "MySQL"          { Test-DbHealthy } 120 | Out-Null
    # API Java hay chết nếu bật trước MySQL (Docker Desktop tự bật lại mọi container cùng lúc) -> tự sửa
    if (-not (Wait-Until "API quản trị" $ApiOk 90)) {
        Say "  -> API lỗi (thường do bật trước MySQL). Khởi động lại container web..." Yellow
        docker restart xiaozhi-esp32-server-web 2>&1 | Out-Null
        Wait-Until "API quản trị (lần 2)" $ApiOk 150 | Out-Null
    }
    # server lấy cấu hình từ API; nếu API vừa được sửa thì server có thể còn kẹt -> tự sửa
    if (-not (Wait-Until "xiaozhi server" $ServerOk 90)) {
        Say "  -> Server chưa nhận được cấu hình. Khởi động lại server..." Yellow
        docker restart xiaozhi-esp32-server 2>&1 | Out-Null
        Wait-Until "xiaozhi server (lần 2)" $ServerOk 150 | Out-Null
    }
    Wait-Until "TTS router"     { & $Checks["TTS router + VOICEVOX"] } 120 | Out-Null

    Show-Status
    Say ("`n  Tổng thời gian: {0:N0} giây" -f ((Get-Date) - $t0).TotalSeconds)
}

function Stop-All {
    Say "===== TẮT SERVER XIAOZHI =====" Cyan
    if (Test-Docker) {
        Say "- Dừng các container xiaozhi..."
        docker @Compose stop 2>&1 | Out-Null
    }
    Say "- Tắt VieNeu-TTS và ASR (giải phóng GPU)..."
    Stop-Port 8010; Stop-Port 8012
    Say "  [OK] Đã tắt. (Docker Desktop và các container khác vẫn giữ nguyên)" Green
}

switch ($Action) {
    "start"   { Start-All }
    "stop"    { Stop-All }
    "restart" { Stop-All; Start-Sleep 3; Start-All }
    "status"  { Show-Status }
}
