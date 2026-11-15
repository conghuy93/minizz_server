# Tạo lối tắt trên Desktop cho bộ công cụ server xiaozhi
$desk = [Environment]::GetFolderPath("Desktop")
$ws = New-Object -ComObject WScript.Shell
$items = @(
  @("Xiaozhi - BAT server",      "START_SERVER.bat",   "imageres.dll,101"),
  @("Xiaozhi - TAT server",      "STOP_SERVER.bat",    "imageres.dll,100"),
  @("Xiaozhi - Khoi dong lai",   "RESTART_SERVER.bat", "shell32.dll,238"),
  @("Xiaozhi - Trang thai",      "STATUS_SERVER.bat",  "shell32.dll,23")
)
foreach ($i in $items) {
  $lnk = $ws.CreateShortcut("$desk\$($i[0]).lnk")
  $lnk.TargetPath = "F:\xiaozhi-server\tools\$($i[1])"
  $lnk.WorkingDirectory = "F:\xiaozhi-server\tools"
  $lnk.IconLocation = "C:\Windows\System32\$($i[2])"
  $lnk.Save()
  Write-Host "Da tao: $desk\$($i[0]).lnk"
}
