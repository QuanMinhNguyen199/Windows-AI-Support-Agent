$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VirtualPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$DesktopLogDir = Join-Path $env:LOCALAPPDATA "WinAssist Local\data\logs"
$DesktopStdoutLog = Join-Path $DesktopLogDir "desktop-stdout.log"
$DesktopStderrLog = Join-Path $DesktopLogDir "desktop-stderr.log"

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    Write-Error "Chưa có .venv. Hãy tạo môi trường và cài requirements-desktop.txt."
}

if (-not (Test-Path -LiteralPath $VirtualPythonw)) {
    Write-Error "Không tìm thấy pythonw.exe trong .venv. Hãy tạo lại môi trường Python."
}

Set-Location -LiteralPath $ProjectRoot
& $VirtualPython -c "import webview" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error (
        "Thiếu dependency desktop. Chạy: " +
        ".\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt"
    )
}

New-Item -ItemType Directory -Path $DesktopLogDir -Force | Out-Null

$DesktopProcess = Start-Process `
    -FilePath $VirtualPythonw `
    -ArgumentList @("-m", "app.desktop") `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $DesktopStdoutLog `
    -RedirectStandardError $DesktopStderrLog `
    -PassThru `
    -Wait

exit $DesktopProcess.ExitCode
