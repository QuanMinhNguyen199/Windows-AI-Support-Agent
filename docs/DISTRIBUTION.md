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
5. Từ bản `0.10.0`, các phiên bản sau được tải, xác minh và cài ngay trong tab
   **Cập nhật WinAssist**; người dùng không phải tự mở file Setup.

## Cập nhật ngay trong ứng dụng

- Bản `0.9.9` và cũ hơn cần cài `0.10.0` thủ công một lần để nhận updater.
- App chỉ chấp nhận URL HTTPS thuộc GitHub Release chính thức của repository.
- SHA-256 lấy từ metadata GitHub phải khớp trước khi installer được đổi tên và chạy.
- File đang tải dùng đuôi `.part` trong `%LOCALAPPDATA%\WinAssist Local\updates`.
- Người dùng có thể hủy khi tải; file tạm được xóa và app hiện đúng trạng thái.
- Sau khi xác minh, installer chạy với `/UPDATE=1`; WinAssist đóng rồi tự mở lại.
- Không tự nâng cấp nếu thiếu checksum, URL sai nguồn hoặc file bị thay đổi.

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

Không tạo release riêng cho sửa lỗi nhỏ, chỉnh chữ hoặc tinh chỉnh giao diện.
Những thay đổi này được gom vào chu kỳ hiện tại và không làm tăng số phiên bản.
Chỉ phát hành khi có thay đổi đáng kể cho người dùng. Trước khi tạo tag, phải
hoàn thiện và duyệt mục `Bản kế tiếp` trong `docs/RELEASE_NOTES.md`; sau khi phát
hành mới đồng bộ nội dung đã duyệt sang Patch Notes trong ứng dụng.

Mỗi phiên bản được phát hành bằng tag tương ứng, ví dụ:

```powershell
git tag v0.10.0
git push origin v0.10.0
```

Bản Beta chưa ký số được ghi rõ trên landing page và release notes. Các bản
stable chỉ phát hành sau khi executable và installer đã ký số.

Workflow `windows-release` sẽ chạy test, build bộ cài, tạo checksum và xuất cả:

- `WinAssist-<version>-Setup.exe` để lưu lịch sử phiên bản.
- `WinAssist-Setup.exe` làm URL tải ổn định cho website.
- Hai file `.sha256` tương ứng.

## Điều kiện trước khi public

- Authenticode hợp lệ trên executable và installer.
- Smoke test Windows 10 và Windows 11 sạch.
- SmartScreen/reputation được kiểm tra bằng certificate phát hành.
- Privacy, license và kênh báo lỗi được liên kết từ landing page.
