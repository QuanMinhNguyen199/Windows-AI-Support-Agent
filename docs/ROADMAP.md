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

Đã hoàn thành Giai đoạn 1–6: safety core, network diagnostics, software catalog,
consent flow, một `AssistantAgent`, Ollama fallback và frontend app hoàn chỉnh
cho MVP. Giai đoạn tiếp theo là hỗ trợ thêm các vấn đề Windows phổ thông.

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

### 4. Software Catalog và Consent — Đã hoàn thành

Catalog MVP gồm một số ứng dụng đã kiểm duyệt:

- Phổ thông: trình duyệt, PDF, LibreOffice, 7-Zip, VLC, Teams/Zoom và bộ gõ
  tiếng Việt phù hợp.
- Kỹ thuật: VS Code, Git, Python, Node.js và Ollama.

Mỗi package cần winget ID chính xác, publisher, category, nguồn và lệnh kiểm tra.
Luồng cài đặt phải tạo pending action, hết hạn sau năm phút và chỉ chạy snapshot
đã lưu khi người dùng xác nhận.

**Hoàn thành khi:** frontend không thể thay command trong bước confirm.

### 5. Local AI — Đã hoàn thành

- Rule-based intent router hỗ trợ tiếng Việt có dấu/không dấu.
- Ollama classification và summary với output schema cố định.
- Một `AssistantAgent` điều phối router và services.
- Tự fallback khi Ollama lỗi, timeout hoặc thiếu model.
- Prompt injection không thể tạo command hay tự xác nhận.

**Hoàn thành khi:** tắt Ollama vẫn dùng được toàn bộ diagnostics.

### 6. Hoàn thiện MVP — Đã hoàn thành

**Frontend application**

- Hoàn thiện frontend thành một ứng dụng có các màn hình/khu vực rõ ràng:
  Chat, Tiện ích, Diagnostics, Software và Activity/History.
- Tạo component/style dùng chung cho app card, status badge, command preview,
  modal xác nhận, notification, empty/loading/error state và progress bar.
- Tạo API client tập trung thay vì gọi `fetch` rải rác; chuẩn hóa timeout, lỗi
  backend, Ollama offline, validation error và request đang chạy.
- Quản lý trạng thái session, pending action và diagnostic run; refresh trang
  không được làm mất action đang theo dõi.
- Render mọi nội dung không tin cậy bằng `textContent`; không render HTML từ LLM,
  command output hoặc API.
- Hỗ trợ responsive, bàn phím, screen reader, focus state và độ tương phản.
- Giữ HTML/CSS/JavaScript thuần cho MVP; chỉ đánh giá framework mới khi độ phức
  tạp thực tế vượt khả năng bảo trì của cấu trúc hiện tại.

**Luồng chức năng**

- Speed-test provider và trạng thái chưa khả dụng.
- Các repair `LOW_RISK`: flush DNS, release/renew IP.
- UI hiển thị bước kiểm tra, kết quả, command preview và confirm/cancel.
- Khu vực **Tiện ích** hiển thị danh sách ứng dụng Windows phổ biến theo nhóm:
  trình duyệt, văn phòng, tiện ích, media và công cụ phát triển.
- Mỗi ứng dụng hiển thị tên, publisher, trạng thái và các biểu tượng hành động
  phù hợp ngay cạnh tên hoặc thanh tiến trình:
  - **Cài đặt:** kiểm tra package, hiển thị command preview rồi yêu cầu xác nhận.
  - **Hủy:** hủy pending action; khi installer đã bắt đầu, chỉ gửi yêu cầu dừng
    an toàn và không force-kill tiến trình nếu có nguy cơ để lại trạng thái lỗi.
  - **Gỡ cài đặt:** hiển thị command winget cố định và chỉ chạy sau xác nhận.
- Cài đặt chạy dưới dạng background action. Frontend theo dõi trạng thái qua
  polling hoặc SSE, không giữ HTTP request confirm mở cho tới khi hoàn tất.
- Progress bar hiển thị các bước `đang chuẩn bị → đang cài → đang xác minh →
  hoàn tất/thất bại`, kèm thời gian đã chạy. Dùng progress không xác định khi
  winget không cung cấp phần trăm; không hiển thị phần trăm/thời gian còn lại giả.
- Icon phải có text/tooltip, trạng thái disabled và nhãn truy cập bàn phím; màu
  sắc không được là dấu hiệu duy nhất để phân biệt hành động.
- Checklist “Thiết lập máy mới” theo nhu cầu: văn phòng, học tập, giải trí,
  họp trực tuyến hoặc lập trình.

**Hoàn thành khi:**

- Các luồng chat → diagnostic và install → confirm/cancel có integration test.
- Chọn app trong Tiện ích không thể bỏ qua command preview và xác nhận.
- UI phản ánh đúng trạng thái action sau refresh và không tạo cài đặt trùng khi
  người dùng bấm icon nhiều lần.
- Cancel pending action không chạy command; install/uninstall đều cần xác nhận.
- Frontend có test cho API client, state transition và DOM rendering; E2E bao phủ
  happy path, Ollama offline, backend lỗi, action hết hạn và thao tác bàn phím.

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
- Frontend quality gate: kiểm tra accessibility tự động, responsive viewport,
  JavaScript lint/test, dependency audit (nếu có) và E2E regression.
- Kiểm tra XSS với message, LLM response, command output và software metadata.
- Đo thời gian hiển thị phản hồi đầu tiên, trạng thái loading và khả năng phục hồi
  UI khi request timeout hoặc backend khởi động lại.
- Threat model cho injection, command spoofing, action replay và data leakage.
- Structured logs local với retention ngắn.

Ngưỡng đề xuất:

- Intent macro F1 ≥ 0,90.
- 100% command ngoài registry bị từ chối.
- Critical diagnostic rule accuracy ≥ 0,95.
- Không còn security issue mức high/critical chưa xử lý.

### 9. Windows Beta

- Bọc frontend web hiện tại trong desktop shell phù hợp sau một technical spike
  (ưu tiên WebView2/pywebview; không viết lại UI nếu không cần).
- Tích hợp window lifecycle, single-instance, icon ứng dụng, system tray tùy chọn,
  mở/đóng backend an toàn và màn hình báo lỗi khi local service chưa sẵn sàng.
- Desktop shell và installer có ký số.
- Cài, nâng cấp, rollback và uninstall.
- Chỉ bind loopback và bảo vệ local API.
- Kiểm thử Windows 10/11 trên máy sạch.
- Export báo cáo đã mask theo lựa chọn người dùng.

**Hoàn thành khi:** người dùng phổ thông có thể cài và mở WinAssist như một ứng
dụng Windows, không cần tự chạy PowerShell hoặc mở URL localhost.

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
