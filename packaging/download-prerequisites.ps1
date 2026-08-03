$ErrorActionPreference = "Stop"
$destination = Join-Path $PSScriptRoot "MicrosoftEdgeWebview2Setup.exe"
$url = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"

if (-not (Test-Path -LiteralPath $destination)) {
    Write-Host "Đang tải Microsoft WebView2 Evergreen Bootstrapper..."
    Invoke-WebRequest -Uri $url -OutFile $destination -UseBasicParsing
}

$signature = Get-AuthenticodeSignature -LiteralPath $destination
if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notmatch "Microsoft") {
    throw "WebView2 bootstrapper không có chữ ký Microsoft hợp lệ."
}
Write-Host "WebView2 bootstrapper đã được xác minh."
