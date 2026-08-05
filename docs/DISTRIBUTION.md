# Phát hành WinAssist cho người dùng phổ thông

## Kênh phát hành Community Beta

- Tên ứng dụng hiển thị: `WinAssist Local`.
- Mục tiêu: phát hành Beta miễn phí để cộng đồng dùng thử và phản hồi.
- Hỗ trợ: `minhquanpro65@gmail.com` và GitHub Issues.
- Project hiện chưa công bố license; cần chọn license trước khi cho phép bên khác
  sao chép, sửa đổi hoặc phân phối lại source code.
- Bản chưa ký số chỉ dùng cho Community Beta có cảnh báo rõ về SmartScreen;
  không mô tả là bản phát hành ổn định hoặc đã được Windows xác minh.

## Trải nghiệm cài đặt

1. Người dùng mở trang tải công khai.
2. Bấm **Tải cho Windows** để nhận `WinAssist-Setup.exe`.
3. Bộ cài tự cài theo tài khoản hiện tại, tạo shortcut và chuẩn bị WebView2.
4. WinAssist tự mở; không cần Python, PowerShell hoặc terminal.
5. Các phiên bản sau được phát hiện trong tab Cập nhật WinAssist.

URL tải cố định:

```text
https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest/download/WinAssist-Setup.exe
```

## GitHub Pages và public domain

Workflow `public-download-page` deploy thư mục `public/` lên GitHub Pages. URL
mặc định dự kiến là:

```text
https://quanminhnguyen199.github.io/Windows-AI-Support-Agent/
```

Để dùng domain riêng:

1. Thêm custom domain trong **Settings → Pages** của repository.
2. Với subdomain như `download.example.com`, tạo DNS `CNAME` trỏ đến
   `quanminhnguyen199.github.io`.
3. Bật **Enforce HTTPS** sau khi GitHub xác minh DNS.
4. Không thêm file `CNAME` cho đến khi đã chọn domain thật.

## Tạo bản phát hành

Chỉ tạo tag công khai sau khi executable và installer đã được ký số:

```powershell
git tag v0.9.7
git push origin v0.9.7
```

Workflow `windows-release` sẽ chạy test, build bộ cài, tạo checksum và xuất cả:

- `WinAssist-0.9.7-Setup.exe` để lưu lịch sử phiên bản.
- `WinAssist-Setup.exe` làm URL tải ổn định cho website.
- Hai file `.sha256` tương ứng.

## Điều kiện trước khi public

- Authenticode hợp lệ trên executable và installer.
- Smoke test Windows 10 và Windows 11 sạch.
- SmartScreen/reputation được kiểm tra bằng certificate phát hành.
- Privacy, license và kênh báo lỗi được liên kết từ landing page.
