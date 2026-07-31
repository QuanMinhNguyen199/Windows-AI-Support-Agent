$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EnvFile = Join-Path $ProjectRoot ".env"

function Get-DotEnvValue {
    param(
        [string]$Name,
        [string]$DefaultValue
    )

    $EnvironmentValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($EnvironmentValue)) {
        return $EnvironmentValue.Trim()
    }

    if (Test-Path -LiteralPath $EnvFile) {
        $MatchedLine = Get-Content -LiteralPath $EnvFile |
            Where-Object { $_ -match "^\s*$([regex]::Escape($Name))\s*=" } |
            Select-Object -Last 1
        if ($MatchedLine) {
            return (($MatchedLine -split "=", 2)[1]).Trim().Trim('"').Trim("'")
        }
    }

    return $DefaultValue
}

function Find-OllamaExecutable {
    $Command = Get-Command ollama -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        "C:\Program Files\Ollama\ollama.exe"
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate) {
            return $Candidate
        }
    }

    return $null
}

function Get-OllamaState {
    param([string]$BaseUrl)

    try {
        $Response = Invoke-RestMethod `
            -Uri "$($BaseUrl.TrimEnd('/'))/api/tags" `
            -Method Get `
            -TimeoutSec 2
        return [PSCustomObject]@{
            Available = $true
            Models = @($Response.models)
        }
    }
    catch {
        return [PSCustomObject]@{
            Available = $false
            Models = @()
        }
    }
}

function Confirm-BootstrapStep {
    param(
        [string]$Mode,
        [string]$Question
    )

    if ($Mode -eq "auto") {
        return $true
    }
    if ($Mode -eq "skip") {
        return $false
    }
    $Answer = Read-Host "$Question [y/N]"
    return $Answer -match "^(?i:y|yes)$"
}

function Select-OllamaModel {
    try {
        $Computer = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
        $MemoryGb = [math]::Round($Computer.TotalPhysicalMemory / 1GB, 1)
    }
    catch {
        $MemoryGb = 8
    }

    if ($MemoryGb -lt 8) {
        return "qwen3:0.6b"
    }
    if ($MemoryGb -lt 16) {
        return "qwen3:1.7b"
    }
    return "qwen3:4b"
}

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Không tìm thấy Python. Hãy cài Python 3.11+ rồi mở lại PowerShell."
    }
    Write-Host "Chưa có môi trường ảo .venv."
    Write-Host "Hãy chạy:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

Set-Location -LiteralPath $ProjectRoot

function Stop-PreviousWinAssistBackend {
    $Listener = Get-NetTCPConnection `
        -LocalPort 8000 `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $Listener) {
        return
    }

    $ExistingProcess = Get-CimInstance `
        -ClassName Win32_Process `
        -Filter "ProcessId = $($Listener.OwningProcess)" `
        -ErrorAction SilentlyContinue
    $ExpectedPython = [IO.Path]::GetFullPath($VirtualPython)
    $CommandLine = [string]$ExistingProcess.CommandLine
    $IsThisProject = (
        $ExistingProcess -and
        $CommandLine.Contains($ExpectedPython, [StringComparison]::OrdinalIgnoreCase) -and
        $CommandLine.Contains(
            "-m uvicorn app.main:app",
            [StringComparison]::OrdinalIgnoreCase
        )
    )
    if (-not $IsThisProject) {
        Write-Error (
            "Port 8000 đang được process khác sử dụng (PID " +
            "$($Listener.OwningProcess)). WinAssist không tự dừng process này."
        )
    }

    Write-Host "Đang dừng backend WinAssist cũ (PID $($Listener.OwningProcess))..."
    Stop-Process -Id $Listener.OwningProcess -ErrorAction Stop
    foreach ($Attempt in 1..20) {
        Start-Sleep -Milliseconds 100
        $StillListening = Get-NetTCPConnection `
            -LocalPort 8000 `
            -State Listen `
            -ErrorAction SilentlyContinue
        if (-not $StillListening) {
            return
        }
    }
    Write-Error "Backend cũ chưa nhả port 8000. Hãy đóng terminal cũ rồi thử lại."
}

Stop-PreviousWinAssistBackend

$BootstrapMode = (Get-DotEnvValue `
    -Name "WINASSIST_OLLAMA_BOOTSTRAP" `
    -DefaultValue "prompt").ToLowerInvariant()
if ($BootstrapMode -notin @("prompt", "auto", "skip")) {
    Write-Warning "WINASSIST_OLLAMA_BOOTSTRAP không hợp lệ; chuyển về prompt."
    $BootstrapMode = "prompt"
}

$OllamaBaseUrl = Get-DotEnvValue `
    -Name "WINASSIST_OLLAMA_BASE_URL" `
    -DefaultValue "http://127.0.0.1:11434"
$ConfiguredOllamaModel = Get-DotEnvValue `
    -Name "WINASSIST_OLLAMA_MODEL" `
    -DefaultValue "auto"
$OllamaModel = if ($ConfiguredOllamaModel.ToLowerInvariant() -eq "auto") {
    Select-OllamaModel
}
else {
    $ConfiguredOllamaModel
}
$env:WINASSIST_OLLAMA_MODEL = $OllamaModel
if ($ConfiguredOllamaModel.ToLowerInvariant() -eq "auto") {
    Write-Host "Đã tự chọn model $OllamaModel theo dung lượng RAM."
}

if ($BootstrapMode -ne "skip") {
    $OllamaExecutable = Find-OllamaExecutable
    if (-not $OllamaExecutable) {
        $ShouldInstall = Confirm-BootstrapStep `
            -Mode $BootstrapMode `
            -Question "Ollama chưa được cài. Cài package Ollama.Ollama bằng winget?"
        if ($ShouldInstall) {
            $Winget = Get-Command winget -ErrorAction SilentlyContinue
            if (-not $Winget) {
                Write-Warning "Không tìm thấy winget; bỏ qua cài Ollama."
            }
            else {
                Write-Host "Đang cài Ollama từ package Ollama.Ollama..."
                & $Winget.Source install `
                    --id Ollama.Ollama `
                    --exact `
                    --accept-source-agreements `
                    --accept-package-agreements
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Cài Ollama không thành công (exit code $LASTEXITCODE)."
                }
                $OllamaExecutable = Find-OllamaExecutable
            }
        }
    }

    $OllamaState = Get-OllamaState -BaseUrl $OllamaBaseUrl
    if ($OllamaExecutable -and -not $OllamaState.Available) {
        Write-Host "Đang khởi động Ollama..."
        Start-Process `
            -FilePath $OllamaExecutable `
            -ArgumentList "serve" `
            -WindowStyle Hidden | Out-Null
        foreach ($Attempt in 1..15) {
            Start-Sleep -Seconds 1
            $OllamaState = Get-OllamaState -BaseUrl $OllamaBaseUrl
            if ($OllamaState.Available) {
                break
            }
        }
    }

    if ($OllamaState.Available) {
        $ModelNames = @(
            $OllamaState.Models | ForEach-Object {
                if ($_.name) { $_.name } elseif ($_.model) { $_.model }
            }
        )
        if ($OllamaModel -notin $ModelNames) {
            $ShouldPull = Confirm-BootstrapStep `
                -Mode $BootstrapMode `
                -Question "Chưa có model $OllamaModel. Tải model này?"
            if ($ShouldPull -and $OllamaExecutable) {
                Write-Host "Đang tải model $OllamaModel..."
                & $OllamaExecutable pull $OllamaModel
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Tải model không thành công (exit code $LASTEXITCODE)."
                }
            }
        }
        else {
            Write-Host "Ollama và model $OllamaModel đã sẵn sàng."
        }
    }
    else {
        Write-Warning "Ollama chưa sẵn sàng; WinAssist sẽ dùng rule-based router."
    }
}

& $VirtualPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
