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

## Quy ước duy trì tài liệu

- README và ROADMAP được cập nhật cùng mọi thay đổi code.
- Patch Note chỉ ghi nhận tính năng lớn, thay đổi hành vi đáng kể, breaking
  change hoặc bản phát hành mới.
- Các tinh chỉnh UI nhỏ được ghi ngắn trong README/ROADMAP, không tăng phiên bản
  và không thêm release note riêng.
- Bản vá nhỏ được gom vào bản phát hành lớn kế tiếp; không tạo tag, release hoặc
  Patch Note riêng. Mọi bản phát hành đáng kể phải soạn và duyệt
  `docs/RELEASE_NOTES.md` trước khi tạo tag.
- Bản WinAssist cũ phải hiển thị cập nhật bắt buộc khi bản mới đã có installer
  chính thức; mất mạng hoặc lỗi máy chủ không được khóa nhầm ứng dụng.
- [x] Bản `0.11.0` thêm cửa sổ cập nhật bắt buộc; từ mốc này, phiên bản cũ bị
  khóa cho tới khi cài xong bản chính thức mới nhất.

## Hiện trạng

Đã hoàn thành Giai đoạn 1–8 và phần mở rộng 8.1: MVP, hỗ trợ Windows phổ thông,
offline eval, security hardening, structured local logging, Windows CI, live
software inventory và Patch Update. Giai đoạn tiếp theo là đóng gói Windows Beta.

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
- Tạo component/style dùng chung cho app card, status badge, notification,
  empty/loading/error state và progress bar. Modal xác nhận dùng câu chữ dễ hiểu;
  command và package ID được thu gọn mặc định trong **Thông tin kỹ thuật**.
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

### 7. Hỗ trợ Windows phổ thông — Đã hoàn thành

Chẩn đoán read-only:

- Thông tin hệ thống, pin và dung lượng.
- Âm thanh, camera, microphone và Bluetooth.
- Máy in và print queue.
- Windows Update, ngày giờ, timezone và startup apps.

Không tự đổi thiết bị mặc định, xóa file/queue, sửa driver hoặc cập nhật Windows.

**Hoàn thành khi:** mỗi nhóm có capability detection, privacy test và trạng thái
“không đủ dữ liệu” thay vì đoán.

### 8. Quality và Security — Đã hoàn thành

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

### 8.1. Live Inventory và Cập nhật WinAssist — Đã hoàn thành

- Theo dõi read-only các khóa Add/Remove Programs cho HKLM/HKCU và ứng dụng
  32-bit/64-bit bằng Windows Registry notification.
- Debounce thay đổi Registry; không chạy `winget list` theo chu kỳ liên tục.
- Gửi sự kiện `software_inventory_changed` đến frontend bằng SSE.
- Tab Tiện ích giữ inventory khi đổi tab, cập nhật action trực tiếp và chỉ quét
  lại sau khi có tín hiệu thay đổi hoặc người dùng yêu cầu.
- Tab **Cập nhật WinAssist** đọc release notes đã version hóa từ
  `data/processed/patch_notes.json`.
- Giữ **Trợ lý** như lối vào phụ giúp người dùng diễn đạt nhu cầu tự nhiên; các
  tab chức năng vẫn là luồng chính, nhanh và có trạng thái rõ ràng.
- Rule-based behavior nhận diện vấn đề hiệu năng mô tả tự nhiên như máy chậm,
  đơ, nóng hoặc mở ứng dụng lâu; phản hồi bằng câu hỏi làm rõ và suggestion có
  thể bấm thay vì tự chạy kiểm tra không liên quan.
- UI thẻ dùng tiêu đề và trạng thái làm trọng tâm; icon chỉ dùng cho điều hướng
  hoặc hành động có ý nghĩa.
- Bootstrap phát hiện và thay thế backend uvicorn cũ của đúng project để frontend
  không gọi nhầm API còn nằm trong bộ nhớ; không tự dừng process ngoài WinAssist.
- Frontend cache-bust asset theo phiên bản, không cache HTML và cho sidebar cuộn
  để các tab mới như Patch Update không biến mất ở màn hình thấp.
- Ứng dụng portable hoặc installer không ghi Uninstall Registry tiếp tục dùng
  executable verification và nút quét thủ công.

**Hoàn thành khi:** cài/gỡ từ Control Panel hoặc installer bên ngoài làm tab
Tiện ích cập nhật mà không cần tải lại trang và không quét nền liên tục.

### 9. Windows Beta — Hoàn thành phần có thể kiểm thử nội bộ

- [x] Bọc frontend hiện tại trong desktop shell pywebview/WebView2, không viết lại UI.
- [x] Quản lý window/backend lifecycle và single-instance bằng Windows mutex.
- [x] Launcher source chạy bằng `pythonw.exe`; cảnh báo runtime được chuyển vào log
  local thay vì hiện trong terminal khi mở app.
- [x] `run.ps1` mặc định mở desktop shell thành cửa sổ riêng; chế độ uvicorn cho
  phát triển API chỉ chạy khi truyền `-ServerOnly`, tránh mở app trong VS Code.
- [x] Giới hạn pywebview JavaScript bridge, không để lộ đối tượng native gây vòng
  lặp `FontFamily/SyncRoot` trong lúc pywebview đăng ký API.
- [x] Mở close dialog ngoài callback native để popup không khóa luồng UI và vẫn
  nhận được thao tác chọn, quay lại hoặc xác nhận.
- [x] Căn giữa cửa sổ theo work area của monitor chứa con trỏ, không che taskbar
  và tự co kích thước trên màn hình nhỏ hoặc cấu hình nhiều monitor.
- [x] Close confirmation hiển thị giữa ứng dụng, dùng lựa chọn có dấu tick cho
  xuống system tray hoặc thoát hoàn toàn; thoát từ tray không hỏi lần hai.
- [x] Hiển thị lỗi native khi backend không sẵn sàng hoặc port bị chiếm.
- [x] Readiness endpoint nhẹ, tách khỏi Ollama health để tránh startup timeout giả.
- [x] Nhận diện GPU NVIDIA/AMD/Intel và điều hướng đến công cụ driver chính hãng.
- [x] Tách Card màn hình và Windows Update thành các tab riêng; dùng câu chữ phổ
  thông thay cho thuật ngữ driver/GPU trên giao diện chính.
- [x] Cập nhật Windows giải thích trạng thái bằng câu chữ phổ thông, sửa định dạng
  ngày bản vá, liệt kê bản cập nhật mới hoặc báo rõ không có bản mới, và mở trực
  tiếp trang cập nhật hệ thống.
- [x] Phân biệt NVIDIA App, AMD Software và Intel Driver Assistant đã cài hay còn
  thiếu; ghi rõ công cụ chính hãng có thể mở cửa sổ/trình duyệt riêng và không
  mô tả nhầm rằng WinAssist đang tự cài driver.
- [x] Tab Cập nhật WinAssist tự kiểm tra GitHub Release và hiển thị release notes.
- [x] Rút gọn Patch Notes cho người dùng phổ thông và thêm form ticket trong tab
  Hỗ trợ: chọn lỗi, mô tả, ảnh tối đa 5 MB và mã `Ticket#...` sau khi gửi email.
- [x] Hoàn thiện trạng thái submit ticket: giữ mã thành công, reset form an toàn
  sau thao tác bất đồng bộ và không hiện thông báo lỗi khi email đã được gửi.
- [x] Thêm language switcher `VI / EN`, lưu lựa chọn local và dịch cả nội dung
  giao diện được tạo động thông qua lớp i18n frontend tập trung.
- [x] Truyền locale vào Chat API và bản địa hóa phản hồi AssistantAgent sau bước
  điều phối, tránh giao diện English nhưng kết luận chẩn đoán vẫn bằng tiếng Việt.
- [x] Tự kiểm tra GitHub Release khi khởi động và thông báo phiên bản mới.
- [x] Nút tải installer trực tiếp; Inno Setup đóng bản cũ và mở lại sau nâng cấp.
- [x] Pipeline theo tag build/test, tạo installer, SHA-256 và đính kèm GitHub Release.
- [x] GitHub Pages landing page, URL tải installer cố định và hướng dẫn custom domain.
- [x] Bộ cài kèm WebView2 Evergreen Bootstrapper đã xác minh chữ ký Microsoft.
- [x] Tạo GitHub Release `v0.9.7` Community Beta với installer ổn định và SHA-256;
  bản này chưa ký số và landing page hiển thị cảnh báo SmartScreen rõ ràng.
- [x] Phát hành patch `0.9.8`: cấu hình backend nhúng chạy được khi bản Windows
  không có terminal, giữ native window ngoài JavaScript bridge để sửa lỗi
  pywebview `ValueError/SyncRoot`, đồng thời ghi traceback vào
  `desktop-crash.log`; installer đã pass smoke test trước khi phát hành.
- [x] Tải nền có progress, kiểm tra SHA-256 và chạy installer trực tiếp trong app.
- [ ] Tải/cài driver có kiểm tra chữ ký số, restore point, progress và rollback.
- [x] Chỉ bind loopback và bảo vệ local API bằng token phiên/cookie HttpOnly.
- [x] Lưu database/log vào `%LOCALAPPDATA%` để tương thích thư mục cài read-only.
- [x] Thêm và chạy thành công PyInstaller onedir spec/script build Windows.
- [x] Spec dùng project root tuyệt đối để bundle static, catalog và prompts.
- [x] Bổ sung icon `.ico` nhất quán và system tray Mở/Ẩn/Thoát.
- [x] Cài Inno Setup 6.7.3, build installer per-user và smoke test cài/gỡ trong
  thư mục cách ly: executable tồn tại, uninstaller exit 0 và xóa sạch thư mục.
- [x] Luôn hiển thị bước chọn thư mục cài đặt; mặc định dùng LocalAppData nhưng
  cho phép chọn ổ/thư mục khác mà người dùng có quyền ghi.
- [x] Thêm tab nhỏ Gỡ WinAssist với xác nhận rõ ràng; chỉ chạy uninstaller nằm
  cạnh executable, xóa dữ liệu WinAssist và giữ nguyên mọi tiện ích đã cài.
- [x] Hotfix `0.10.1`: chờ tiến trình WinAssist thoát hoàn toàn trước khi chạy
  uninstaller và dọn thư mục cài đặt, tránh sót `WinAssist.exe` hoặc `_internal`.
- [ ] Ký số desktop shell và installer bằng certificate phát hành.
- [ ] Kiểm thử Windows 10/11 trên máy sạch và pipeline release artifact.
- [x] Tinh gọn Tổng quan máy; loại bỏ chức năng xuất báo cáo JSON không cần thiết.
- [x] Sửa layout Trợ lý theo viewport: chat log tự co giãn, composer luôn hiển
  thị đủ và không làm trang bị tràn margin/scrollbar dọc ngoài ý muốn.
- [x] Chọn hướng Community Beta, dùng `minhquanpro65@gmail.com` và GitHub Issues
  làm kênh hỗ trợ; chưa công bố license và phải cảnh báo rõ nếu installer chưa ký số.

Các mục còn mở phụ thuộc phát hành hoặc có rủi ro hệ thống cao: certificate ký
số, ma trận máy sạch Windows 10/11, updater tải/chạy nền có rollback và cài
driver có restore point. Không đánh dấu hoàn thành cho đến khi kiểm thử thực tế.

**Hoàn thành khi:** người dùng phổ thông có thể cài và mở WinAssist như một ứng
dụng Windows, không cần tự chạy PowerShell hoặc mở URL localhost.

### 10. Release 1.0

- [x] Self-updater tải nền ngay trong app, hiển thị progress thật, cho phép hủy,
  bắt buộc xác minh SHA-256 và tự mở lại WinAssist sau khi cài.

- [x] Rút gọn README thành trang giới thiệu sản phẩm dễ đọc; chuyển hướng dẫn
  kỹ thuật chi tiết sang thư mục `docs/`.
- [x] Trợ lý hiển thị danh sách ứng dụng cơ bản khi yêu cầu cài đặt còn chung
  chung; `Enter` gửi tin nhắn và `Shift+Enter` xuống dòng.
- [x] Làm mới website tải WinAssist với giao diện responsive, giới thiệu tính
  năng, hướng dẫn ba bước và ghi chú phiên bản dễ hiểu ngay trên trang.
- [x] Chuẩn hóa scrollbar và khoảng cách vùng cuộn trên mọi tab desktop.
- [x] Phát hành `0.9.9 Hotfix` cho scrollbar và khoảng cách giao diện.
- [x] Hiển thị tổng lượt tải installer thật từ GitHub Release trên website.
- [x] Tạo backlog `FUTURE_APP_CATALOG.md` cho tiện ích phổ thông và chuyên sâu
  theo nghề; mỗi app phải qua kiểm tra nguồn, publisher và hành vi installer.

- Cài Windows Update trực tiếp trong WinAssist qua API hệ thống được hỗ trợ, có
  yêu cầu quyền Administrator rõ ràng, progress thật, xác nhận trước khi cài,
  xử lý yêu cầu khởi động lại và không báo thành công trước khi Windows xác nhận.
- Onboarding AI local ở lần mở đầu tiên, không cài AI âm thầm trong setup.
- Quét RAM, CPU, GPU và dung lượng trống trước khi đề xuất model Qwen.
- Đề xuất `qwen3:0.6b`, `qwen3:1.7b` hoặc `qwen3:4b` theo cấu hình máy.
- Cho phép chọn **Bật AI local** hoặc **Dùng chế độ cơ bản**; ghi nhớ lựa chọn
  và không nhắc lại liên tục.
- Khi bật AI: tự cài Ollama, tải model với dung lượng dự kiến, progress, hủy,
  tiếp tục, thử lại và xác minh model trước khi báo hoàn tất.
- Có phần quản lý AI local để bật sau, đổi model hoặc gỡ model/Ollama có xác nhận.
- Rule-based router luôn hoạt động khi người dùng bỏ qua AI hoặc cài đặt thất bại.
- Thêm mục **Dọn dẹp máy** theo hai bước: quét read-only và hiển thị dung lượng
  trước; sau đó cho tick từng nhóm file tạm an toàn và xác nhận mới xóa. MVP ưu
  tiên file tạm người dùng, thumbnail cache, crash dump cũ và mở Storage Sense.
- Không chọn sẵn Thùng rác; không đụng Downloads, Documents, Desktop, Windows
  Installer cache, restore point, driver package hoặc file đang được sử dụng.
- Mọi thao tác dọn dẹp phải đi qua `command_registry`, `command_runner` và
  `risk_policy`, ghi dung lượng thực tế đã xóa; AssistantAgent chỉ điều phối.
- Ổn định API và database migration.
- Recovery khi database hỏng hoặc thiếu model.
- Catalog/troubleshooting rules có version và quy trình review.
- Security review, tài liệu người dùng và release process hoàn chỉnh.

Trước khi bắt đầu Giai đoạn 10, tiếp tục mở rộng catalog **Tiện ích**, kiểm tra
package ID/publisher và tinh chỉnh UI/UX của bản Beta. Các thay đổi này không yêu
cầu đổi backend AI hiện tại.

- [x] Thêm nhóm Game & giải trí với package Winget đã xác minh: Steam, Epic,
  GOG, Discord, EA, Ubisoft, League of Legends VN2 và VALORANT AP; cài trực tiếp
  qua Safety Core sau xác nhận, không mở trang tải và không chạy command từ agent.
- [x] Gộp League of Legends và VALORANT vào một card Riot Games trên giao diện,
  đồng thời giữ package/action riêng để người dùng chủ động chọn đúng game.
- [x] Bỏ tên máy chủ Riot khỏi giao diện và xác minh trạng thái từ
  `RiotClientInstalls.json` cùng executable thực tế, tránh báo chưa cài khi game
  nằm ở ổ khác hoặc Riot đã tự chuyển vùng tài khoản.
- [x] Mở rộng catalog lên 57 ứng dụng: thêm nhóm liên lạc, lưu trữ đám mây, sáng
  tạo nội dung và các công cụ Docker/database/SSH/phân tích mạng phổ biến; chỉ
  nhận package Winget đã xác minh được ID và publisher.
- [x] Bổ sung Brave, Opera, Vivaldi và LibreWolf cho người dùng muốn trình duyệt
  có sẵn khả năng giảm quảng cáo/theo dõi; không tự cài extension trình duyệt.
- [x] Sắp xếp app thường dùng lên đầu từng nhóm bằng rank trong catalog; giữ
  nguyên hai tab Phổ thông/Chuyên sâu và không tạo danh sách máy mới bị trùng.
- [x] Bổ sung IDE/công cụ AI chính chủ: Cursor, Antigravity IDE, Windsurf, Zed,
  Sublime Text, Visual Studio Community và OpenAI Codex CLI; phân biệt rõ IDE
  với công cụ dòng lệnh trong tên và ghi chú license.
- [x] Giữ hai tab Phổ thông/Chuyên sâu và chia tab Chuyên sâu theo bốn nhu cầu:
  Lập trình, Marketing & sáng tạo, Văn phòng chuyên sâu, Quản trị hệ thống; hỗ
  trợ một package xuất hiện ở nhiều ngữ cảnh nhưng không nhân đôi action/status.
- [x] Thêm mô tả ngắn, dễ hiểu cho toàn bộ card Tiện ích; mô tả được quản lý
  trong software catalog và trả về qua API, không hardcode theo tên ở frontend.
- [x] Xác minh Discord bằng file cài đặt thực tế ngoài kết quả Winget tổng, xử lý
  trường hợp Winget trả ARP ID khác package ID chuẩn.

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
- Tự gỡ/cài driver không có xác nhận, restore point hoặc khả năng rollback.
- Tự xóa file hoặc dữ liệu người dùng khi chưa quét, phân loại và xác nhận rõ.
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
