$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Không tìm thấy Python. Hãy cài Python 3.11+ rồi mở lại PowerShell."
}

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    Write-Host "Chưa có môi trường ảo .venv."
    Write-Host "Hãy chạy:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

Set-Location -LiteralPath $ProjectRoot
& $VirtualPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
