# Windows Beta

## Phạm vi hiện tại

WinAssist `0.9.7` có desktop shell chạy frontend hiện tại trong WebView2 thông
qua pywebview. Shell khởi động FastAPI trên `127.0.0.1:8000`, chờ health check,
mở cửa sổ và yêu cầu backend dừng khi cửa sổ đóng.

Shell chờ `/api/ready`, không chờ `/api/health`; readiness chỉ xác nhận FastAPI
sẵn sàng, trong khi health đầy đủ còn gọi Ollama và có thể phản hồi chậm.

## Chạy từ source

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\run-desktop.ps1
```

Nếu port 8000 đang bị backend web cũ chiếm, đóng terminal đó trước khi mở desktop
app. Single-instance mutex ngăn hai desktop shell chạy đồng thời.

## Build

```powershell
.\build-windows.ps1
```

PyInstaller tạo bundle onedir tại `dist\WinAssist`. Bundle gồm frontend static,
catalog đã xử lý, prompts và runtime pywebview. Onedir được chọn cho Beta để dễ
kiểm tra file, startup nhanh hơn onefile và hỗ trợ rollback bằng thư mục release.

Build `0.9.7` đã được xác minh tạo executable và đủ static/catalog/prompt trên
Windows 11 với Python 3.14, pywebview 6.2.1 và PyInstaller 6.21.0. Việc mở GUI và
luồng cài/gỡ vẫn phải smoke-test trên máy sạch trước khi phát hành.

## Installer nội bộ

`packaging/WinAssist.iss` định nghĩa installer per-user, shortcut Start Menu,
desktop shortcut tùy chọn và uninstall entry. Chạy:

```powershell
.\build-installer.ps1
```

Script dùng Inno Setup 6.7.3 và installer 0.9.7 đã smoke test cài/gỡ thành công
trong thư mục cách ly. Installer không xóa database/log trong
`%LOCALAPPDATA%\WinAssist Local`; lựa chọn xóa dữ liệu sẽ được thiết kế riêng.

## Bảo vệ local API

- Backend chỉ bind `127.0.0.1`.
- Shell sinh token ngẫu nhiên cho mỗi lần mở.
- Trang bootstrap đổi token thành cookie `HttpOnly`, `SameSite=Strict`.
- API ngoài health check trả `403` nếu thiếu cookie đúng.
- Token không được ghi vào log request.

## Dữ liệu runtime

Database và log được ghi tại `%LOCALAPPDATA%\WinAssist Local\data`, không ghi vào
bundle hoặc `Program Files`. Gỡ ứng dụng không được tự xóa dữ liệu người dùng;
installer tương lai phải cung cấp lựa chọn xóa dữ liệu rõ ràng.

## Điều kiện trước khi phát hành công khai

1. Icon `.ico` và system tray đã được bổ sung.
2. Tạo installer hỗ trợ install, upgrade, rollback và uninstall.
3. Ký số executable và installer bằng certificate hợp lệ.
4. Kiểm thử Windows 10 và 11 trên máy sạch, cả tài khoản standard user.
5. Release pipeline đã lưu SHA-256; còn cần certificate phát hành để ký binary.

## Kết quả smoke test 0.9.4

- Inno Setup 6.7.3 build thành công installer per-user.
- Cài silent vào thư mục cách ly tạo đủ `WinAssist.exe` và uninstaller.
- Gỡ silent trả exit code 0 và xóa sạch thư mục thử nghiệm.
- Authenticode hiện là `NotSigned`; không phát hành công khai trước khi có certificate.
- Installer online 0.9.4 kèm WebView2 bootstrapper có chữ ký Microsoft; smoke
  test lại sau đóng gói cho kết quả install/uninstall exit code 0.
- Installer 0.9.5 giữ URL `WinAssist-Setup.exe` đồng bộ với bản versioned;
  checksum trùng khớp, install/uninstall exit code 0 và xóa sạch target thử nghiệm.
- Installer 0.9.6 tiếp tục smoke test thành công; stable installer khớp hash với
  bản versioned và target thử nghiệm được gỡ sạch.
- Installer 0.9.7 có tab Windows Update riêng và tiếp tục đạt smoke test cài/gỡ;
  stable installer khớp bản versioned.

Build từ `build-windows.ps1` hiện là Beta nội bộ, chưa được ký số.

## Community Beta 0.9.7

- GitHub Release: `v0.9.7`.
- Pipeline Windows sạch trên GitHub Actions đã test, build PyInstaller/Inno Setup,
  tạo SHA-256 và upload đủ installer versioned/stable.
- GitHub Pages và URL `releases/latest/download/WinAssist-Setup.exe` trả về bình thường.
- Bản phát hành chưa ký số nên SmartScreen có thể cảnh báo.
- Còn phải kiểm thử Windows 10/11 sạch, standard user và ký số trước bản stable.
