# Threat model

## Tài sản cần bảo vệ

- Quyền thực thi command trên máy Windows.
- Nội dung chat, thông tin thiết bị và lịch sử action local.
- Tính toàn vẹn của software catalog, command registry và pending action snapshot.

## Trust boundaries

- Trình duyệt ↔ FastAPI loopback.
- FastAPI/agent ↔ Ollama local.
- Services ↔ command runner ↔ Windows.
- Catalog/prompt/eval files ↔ runtime.

## Mối đe dọa và kiểm soát

| Mối đe dọa | Kiểm soát |
|---|---|
| Prompt injection tạo command | Agent không tạo command; registry là allowlist cố định |
| Thay command lúc confirm | Backend chạy snapshot và đối chiếu registry hiện tại |
| Action replay | State transition nguyên tử trong SQLite; action chỉ confirm một lần |
| Cài package giả | Exact winget ID, publisher/source trong catalog |
| XSS từ LLM/output | Frontend chỉ dùng `textContent`; CSP chặn inline script |
| Rò dữ liệu qua log | Không log body/query/output; redaction trước khi lưu chat |
| Truy cập camera/microphone | Chỉ đọc metadata PnP; Permissions-Policy chặn web API |
| Lệnh treo/output lớn | Timeout, output limit và subprocess `shell=False` |
| Clickjacking/MIME sniffing | `X-Frame-Options`, CSP và `nosniff` |
| Dependency compromise | Pin major range, CI `pip-audit`, review lock/version khi release |
| Updater tải file giả | Chỉ cho phép GitHub Release chính thức; bắt buộc SHA-256 từ metadata release |
| File cập nhật bị đổi sau tải | Kiểm tra lại SHA-256 ngay trước khi chạy installer |
| Path traversal qua version/URL | Version theo mẫu số cố định; tên file và thư mục update do app tự tạo |

## Không tự động thực hiện

- Tắt Defender hoặc Firewall.
- Sửa Registry, driver, Windows Update hoặc thiết bị mặc định.
- Xóa file, print queue hoặc dữ liệu người dùng.
- Đọc nội dung file, tên tài liệu in, camera hay microphone stream.
