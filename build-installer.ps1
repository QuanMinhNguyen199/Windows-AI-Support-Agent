$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildScript = Join-Path $ProjectRoot "build-windows.ps1"
$InstallerScript = Join-Path $ProjectRoot "packaging\WinAssist.iss"
$PrerequisiteScript = Join-Path $ProjectRoot "packaging\download-prerequisites.ps1"
$Candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$Compiler = $Candidates |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1

if (-not $Compiler) {
    Write-Error (
        "Không tìm thấy Inno Setup 6 (ISCC.exe). " +
        "Hãy cài Inno Setup từ jrsoftware.org rồi chạy lại."
    )
}

& $BuildScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build executable thất bại; không tạo installer."
}

& $PrerequisiteScript

& $Compiler $InstallerScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build installer không thành công."
}

$VersionedInstaller = Get-ChildItem (Join-Path $ProjectRoot "dist\installer") `
    -Filter "WinAssist-*-Setup.exe" |
    Where-Object { $_.Name -ne "WinAssist-Setup.exe" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$StableInstaller = Join-Path $ProjectRoot "dist\installer\WinAssist-Setup.exe"
Copy-Item -LiteralPath $VersionedInstaller.FullName -Destination $StableInstaller -Force
$Hash = (Get-FileHash -LiteralPath $VersionedInstaller.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $($VersionedInstaller.Name)" | Set-Content "$($VersionedInstaller.FullName).sha256" -Encoding ascii
"$Hash  WinAssist-Setup.exe" | Set-Content "$StableInstaller.sha256" -Encoding ascii

Write-Host "Installer đã tạo trong dist\installer."
Write-Warning "Installer chưa ký số; chỉ dùng để kiểm thử nội bộ."
