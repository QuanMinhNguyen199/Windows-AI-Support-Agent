$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    Write-Error "Chưa có .venv. Hãy tạo môi trường và cài requirements-desktop.txt."
}

Set-Location -LiteralPath $ProjectRoot
& $VirtualPython -c "import webview" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error (
        "Thiếu dependency desktop. Chạy: " +
        ".\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt"
    )
}

& $VirtualPython -m app.desktop
