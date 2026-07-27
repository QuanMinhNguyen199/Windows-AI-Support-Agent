# WinAssist Local — Roadmap

## Mục tiêu

Phát triển WinAssist Local thành Windows AI Support Agent chạy local cho cả
người dùng phổ thông và người dùng kỹ thuật.

Sản phẩm sẽ hỗ trợ:

- Thiết lập máy mới và cài ứng dụng từ whitelist.
- Chẩn đoán mạng, Wi-Fi, DNS, ping và packet loss.
- Kiểm tra các vấn đề Windows thường gặp.
- Giải thích kết quả bằng tiếng Việt.
- Chỉ thay đổi hệ thống sau khi người dùng xác nhận.

Roadmap này là định hướng, không phải lịch phát hành cố định.

## Hiện trạng

Đã có:

- FastAPI server và giao diện chatbot cơ bản.
- Health endpoint và cấu hình môi trường.
- Script chạy local.
- Hai smoke test.

Chưa có:

- Command registry, risk policy và command runner.
- Chat API, diagnostics và SQLite.
- Software catalog và pending actions.
- `AssistantAgent`, Ollama và rule-based router.
- AI evals, CI và Windows installer.

## Nguyên tắc bắt buộc

1. Chỉ chạy command đã định nghĩa trong registry.
2. Agent và LLM không được tạo hoặc chạy shell command.
3. Hành động `LOW_RISK` cần xác nhận; `HIGH_RISK` không tự chạy trong MVP.
4. Ollama lỗi không được làm hỏng chức năng rule-based.
5. Kết luận phải dựa trên kết quả kiểm tra thực tế.
6. Dữ liệu nhạy cảm phải được mask trước khi lưu.
7. Không truy cập nội dung file, camera hoặc microphone của người dùng.

## Các giai đoạn

### 1. Foundation — Đã hoàn thành

- FastAPI, giao diện tĩnh, health check và cấu hình.
- Script chạy và smoke test.

### 2. Safety Core — Đã hoàn thành

- Tạo `RiskLevel`, command registry và command runner.
- Dùng `list[str]`, `shell=False`, timeout và output limit.
- Chặn executable/argument không nằm trong allowlist.
- Test timeout, command không tồn tại và validation.

**Hoàn thành khi:** không có đường chạy raw command ngoài safety core.

### 3. Network Diagnostics — Đã hoàn thành

- Adapter, IP, DHCP và default gateway.
- Ping, packet loss, DNS và Wi-Fi.
- Parser dùng fixture, không gọi mạng thật trong unit test.
- Trả observation, likely cause, confidence và next steps.

**Hoàn thành khi:** phân biệt được lỗi adapter, DHCP, gateway, Internet và DNS.

### 4. Software Catalog và Consent

Catalog MVP gồm một số ứng dụng đã kiểm duyệt:

- Phổ thông: trình duyệt, PDF, LibreOffice, 7-Zip, VLC, Teams/Zoom và bộ gõ
  tiếng Việt phù hợp.
- Kỹ thuật: VS Code, Git, Python, Node.js và Ollama.

Mỗi package cần winget ID chính xác, publisher, category, nguồn và lệnh kiểm tra.
Luồng cài đặt phải tạo pending action, hết hạn sau năm phút và chỉ chạy snapshot
đã lưu khi người dùng xác nhận.

**Hoàn thành khi:** frontend không thể thay command trong bước confirm.

### 5. Local AI

- Rule-based intent router hỗ trợ tiếng Việt có dấu/không dấu.
- Ollama classification và summary với output schema cố định.
- Một `AssistantAgent` điều phối router và services.
- Tự fallback khi Ollama lỗi, timeout hoặc thiếu model.
- Prompt injection không thể tạo command hay tự xác nhận.

**Hoàn thành khi:** tắt Ollama vẫn dùng được toàn bộ diagnostics.

### 6. Hoàn thiện MVP

- Speed-test provider và trạng thái chưa khả dụng.
- Các repair `LOW_RISK`: flush DNS, release/renew IP.
- UI hiển thị bước kiểm tra, kết quả, command preview và confirm/cancel.
- Checklist “Thiết lập máy mới” theo nhu cầu: văn phòng, học tập, giải trí,
  họp trực tuyến hoặc lập trình.

**Hoàn thành khi:** các luồng chat → diagnostic và install → confirm/cancel có
integration test.

### 7. Hỗ trợ Windows phổ thông

Chẩn đoán read-only:

- Thông tin hệ thống, pin và dung lượng.
- Âm thanh, camera, microphone và Bluetooth.
- Máy in và print queue.
- Windows Update, ngày giờ, timezone và startup apps.

Không tự đổi thiết bị mặc định, xóa file/queue, sửa driver hoặc cập nhật Windows.

**Hoàn thành khi:** mỗi nhóm có capability detection, privacy test và trạng thái
“không đủ dữ liệu” thay vì đoán.

### 8. Quality và Security

- Eval intent, diagnostic accuracy và safety.
- CI, lint, type check, coverage và dependency scan.
- Threat model cho injection, command spoofing, action replay và data leakage.
- Structured logs local với retention ngắn.

Ngưỡng đề xuất:

- Intent macro F1 ≥ 0,90.
- 100% command ngoài registry bị từ chối.
- Critical diagnostic rule accuracy ≥ 0,95.
- Không còn security issue mức high/critical chưa xử lý.

### 9. Windows Beta

- Desktop shell và installer có ký số.
- Cài, nâng cấp, rollback và uninstall.
- Chỉ bind loopback và bảo vệ local API.
- Kiểm thử Windows 10/11 trên máy sạch.
- Export báo cáo đã mask theo lựa chọn người dùng.

### 10. Release 1.0

- Ổn định API và database migration.
- Recovery khi database hỏng hoặc thiếu model.
- Catalog/troubleshooting rules có version và quy trình review.
- Security review, tài liệu người dùng và release process hoàn chỉnh.

## Thứ tự phụ thuộc

```text
Safety Core
  → Network + Software
    → Local AI
      → Complete MVP
        → General Windows Support
          → Quality/Security
            → Windows Beta
              → 1.0
```

AI không được điều phối tool trước khi Safety Core hoàn thành. Packaging chỉ bắt
đầu khi API và data model của MVP tương đối ổn định.

## Ngoài phạm vi gần

- Tự sửa Registry.
- Tắt Defender hoặc Firewall.
- Tự gỡ/cài driver.
- Tự xóa file hoặc dữ liệu người dùng.
- Chạy script do LLM tạo.
- Remote administration.

## Mốc dự kiến

| Mốc | Kết quả |
|---|---|
| M0 | Foundation hiện tại |
| M1 | Safety Core |
| M2 | Network và software workflows |
| M3 | AI-assisted MVP |
| M4 | Hỗ trợ Windows phổ thông |
| M5 | Hardened MVP |
| M6 | Windows Beta |
| M7 | Stable 1.0 |

Ước tính đến Beta: khoảng **13–17 sprint** cho nhóm nhỏ. Ước tính cần được cập
nhật sau Safety Core và thử nghiệm parser trên nhiều phiên bản/ngôn ngữ Windows.
