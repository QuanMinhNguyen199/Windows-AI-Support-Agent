$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$output = Join-Path $PSScriptRoot "WinAssist.ico"
if (Test-Path -LiteralPath $output) {
    Write-Host "Sử dụng icon hiện có tại $output"
    exit 0
}
$bitmap = [System.Drawing.Bitmap]::new(256, 256)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::FromArgb(15, 30, 48))

$accent = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(84, 217, 238))
$white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
$graphics.FillEllipse($accent, 28, 28, 200, 200)
$font = [System.Drawing.Font]::new("Segoe UI", 112, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$format = [System.Drawing.StringFormat]::new()
$format.Alignment = [System.Drawing.StringAlignment]::Center
$format.LineAlignment = [System.Drawing.StringAlignment]::Center
$graphics.DrawString("W", $font, $white, [System.Drawing.RectangleF]::new(28, 20, 200, 208), $format)

$handle = $bitmap.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($handle)
$stream = [System.IO.File]::Create($output)
$icon.Save($stream)
$stream.Dispose()
$icon.Dispose()
$font.Dispose()
$format.Dispose()
$accent.Dispose()
$white.Dispose()
$graphics.Dispose()
$bitmap.Dispose()
Write-Host "Đã tạo $output"
