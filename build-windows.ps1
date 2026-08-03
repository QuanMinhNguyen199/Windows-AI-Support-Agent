$ErrorActionPreference = "Stop"
$IconScript = Join-Path $PSScriptRoot "packaging\create-icon.ps1"
& $IconScript
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecPath = Join-Path $ProjectRoot "packaging\WinAssist.spec"

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    Write-Error "Chưa có .venv. Không thể build Windows Beta."
}

Set-Location -LiteralPath $ProjectRoot
& $VirtualPython -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Không thể cài dependency desktop/build."
}

& $VirtualPython -m PyInstaller --noconfirm --clean $SpecPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build không thành công."
}

Write-Host "Build hoàn tất tại dist\WinAssist\WinAssist.exe"
Write-Warning "Binary Beta chưa được ký số. Không phát hành công khai trước khi ký và kiểm thử."
