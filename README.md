# WinAssist Local

> **Cài Community Beta cho Windows:** tải một file tại
> [WinAssist-Setup.exe](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest/download/WinAssist-Setup.exe).
> Không cần Python, PowerShell hoặc terminal. Bản 0.9.7 chưa ký số nên Windows
> SmartScreen có thể cảnh báo; chỉ tải từ trang chính thức hoặc GitHub Release.

WinAssist Local là trợ lý hỗ trợ Windows chạy trên máy người dùng. Ứng dụng hướng
tới hai nhóm nhu cầu:

- Người dùng phổ thông: cài ứng dụng cơ bản, kiểm tra Wi-Fi, DNS, âm thanh,
  camera, Bluetooth, máy in, dung lượng và Windows Update.
- Người dùng kỹ thuật: kiểm tra/cài VS Code, Git, Python, Node.js và Ollama.

Ứng dụng ưu tiên kiểm tra read-only. Mọi hành động thay đổi hệ thống phải được
hiển thị trước và chỉ chạy sau khi người dùng xác nhận.

Project đang được chuẩn bị dưới dạng **Community Beta** để phục vụ cộng đồng.
Kênh hỗ trợ: [minhquanpro65@gmail.com](mailto:minhquanpro65@gmail.com) hoặc
[GitHub Issues](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/issues).
Project hiện chưa công bố license; việc public source code không tự động cấp
quyền sao chép, sửa đổi hoặc phân phối lại. Installer Beta chưa ký số có thể bị
Windows SmartScreen hiển thị cảnh báo.

Community Beta đầu tiên: [WinAssist 0.9.7](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/tag/v0.9.7).

## Trạng thái hiện tại

Project đã hoàn thành **Giai đoạn 1–8** và nền tảng **Giai đoạn 9 Windows Beta**:

- FastAPI server.
- Giao diện chatbot HTML/CSS/JavaScript.
- `GET /api/health`.
- `GET /api/ready` cho desktop startup, không chờ kiểm tra Ollama.
- Safety core gồm command registry, risk policy và command runner.
- Chẩn đoán IP, gateway, ping, packet loss, DNS và Wi-Fi.
- `POST /api/diagnostics/network` và `POST /api/diagnostics/ping`.
- Software catalog gồm 23 ứng dụng phổ thông/kỹ thuật đã kiểm duyệt.
- Kiểm tra phần mềm, tạo pending install action và confirm/cancel bằng SQLite.
- `POST /api/chat`, một `AssistantAgent`, Ollama structured output và rule-based
  fallback tiếng Việt có dấu/không dấu.
- Chat history tối thiểu trong SQLite, có redaction cho MAC, username,
  password/token phổ biến.
- Cấu hình qua biến môi trường `WINASSIST_*`.
- Unit/integration test dùng fixture và mock, không chạy mạng thật.
- Giao diện app gồm Chat, Tiện ích, Diagnostics và Activity.
- Tab Trợ lý dùng layout co giãn theo chiều cao cửa sổ; khung hội thoại cuộn bên
  trong và ô nhập luôn nằm gọn phía dưới, không tạo khoảng tràn toàn trang.
- Màn hình Tổng quan máy luôn mở trước, hiển thị Windows, CPU, RAM, GPU và ổ hệ thống.
- Mục Chẩn đoán nhận diện GPU NVIDIA/AMD/Intel, hiển thị phiên bản driver và
  mở đúng công cụ cập nhật chính hãng. WinAssist không tự chạy driver installer
  vì màn hình có thể chớp hoặc máy có thể cần khởi động lại.
- “Card màn hình” và “Windows Update” có tab độc lập; tab cập nhật
  ứng dụng vẫn chỉ dùng để cập nhật chính WinAssist.
- Tab **Cập nhật Windows** giải thích lần cập nhật gần nhất và yêu cầu khởi động
  lại bằng câu chữ phổ thông, đồng thời dùng Windows Update API để liệt kê các
  bản mới đang chờ hoặc báo rõ **không có bản cập nhật mới**. Sau đó app mở đúng
  Windows Settings để người dùng cài.
  Bản hiện tại chưa tự cài cập nhật hệ thống trực tiếp trong WinAssist.
- Sau khi kiểm tra card màn hình, WinAssist ghi rõ NVIDIA App, AMD Software hoặc
  Intel Driver Assistant đã có trên máy hay chưa. Nếu đã có, app mở đúng công cụ;
  nếu chưa có, app mở trang tải chính hãng và báo trước rằng công cụ có thể tiếp
  tục bằng cửa sổ hoặc trình duyệt riêng. WinAssist chưa tự cài driver trực tiếp.
- Desktop có icon riêng và system tray với Mở, Ẩn, Thoát.
- Tab **Gỡ WinAssist** gọi đúng Inno uninstaller sau xác nhận, xóa thư mục cài
  và dữ liệu riêng của WinAssist; các ứng dụng đã cài từ Tiện ích không bị ảnh hưởng.
- Bộ cài luôn hiển thị bước chọn thư mục, cho phép người dùng đổi sang ổ hoặc
  thư mục khác; mặc định vẫn dùng `%LOCALAPPDATA%\Programs\WinAssist` để không
  yêu cầu quyền Administrator.
- Pipeline Windows Release chạy test, build PyInstaller/Inno Setup, tạo SHA-256
  và đính kèm artifact khi push tag. Installer 0.9.7 đã qua smoke test cài/gỡ;
  bản hiện tại chưa ký số nên chỉ dùng nội bộ.
- GitHub Pages có landing page tối giản và URL tải cố định; installer đóng gói
  WebView2 Evergreen Bootstrapper đã xác minh chữ ký Microsoft để máy Windows
  10/11 không phải tự cài runtime giao diện.
- WinAssist tự kiểm tra GitHub Release khi khởi động. Tab Cập nhật WinAssist hiển thị
  phiên bản mới và nút tải installer; installer có thể đóng bản cũ, nâng cấp và
  mở lại ứng dụng mà không cần chạy lại terminal. Repository cần có GitHub
  Release với asset tên `WinAssist-<version>-Setup.exe` để luồng này hoạt động.
- Cài/gỡ ứng dụng chạy nền, có hộp xác nhận bằng ngôn ngữ đơn giản; command và
  package ID được thu gọn trong **Thông tin kỹ thuật**, hỗ trợ hủy pending action,
  trạng thái và progress không xác định.
- Nhóm **Game & giải trí** có Steam, Epic Games Launcher, GOG GALAXY, Discord,
  EA app, Ubisoft Connect, League of Legends và VALORANT. WinAssist
  tải installer qua Winget sau xác nhận, không chuyển người dùng sang trang tải;
  launcher game vẫn có thể yêu cầu đăng nhập, tải thêm dữ liệu hoặc khởi động lại.
  League of Legends và VALORANT được gộp trong một card **Riot Games**, nhưng giữ
  hai nút cài riêng để không tải nhầm game; cả hai dùng chung Riot Client. Trạng
  thái được xác minh từ cấu hình Riot và file game thực tế trên mọi ổ đĩa, không
  phụ thuộc package ID khu vực mà Winget đã dùng lúc cài.
- Catalog hiện có 57 ứng dụng. Nhóm Phổ thông bổ sung Telegram, Google Drive,
  Dropbox, Notion, OBS Studio, WinRAR và Canva. Nhóm Chuyên sâu bổ sung Docker
  Desktop, JetBrains Toolbox, DBeaver, WinSCP, PuTTY, Wireshark, VirtualBox và
  GitHub CLI. WhatsApp chưa được thêm vì hiện không có package community chính
  thức phù hợp với nguồn Winget mà WinAssist đang cho phép.
- Mục Trình duyệt trong Phổ thông có thêm Brave, Opera, Vivaldi và LibreWolf.
  Mô tả dùng từ “giảm/chặn quảng cáo và theo dõi” thay vì cam kết chặn mọi quảng
  cáo, vì hiệu quả còn phụ thuộc website và thiết lập của từng trình duyệt.
- Ứng dụng trong mỗi nhóm được sắp xếp bằng `display_rank`: lựa chọn thường dùng
  nằm trước để giảm cuộn trang, nhưng không tạo nhóm “máy mới”, không nhân đôi
  card và không tự cài bất kỳ ứng dụng nào.
- Nhóm IDE và công cụ AI gồm Cursor, Antigravity IDE, Windsurf, Zed, Sublime
  Text 4, Visual Studio Community 2022 và Codex CLI. Codex được ghi rõ là công
  cụ dòng lệnh, không phải IDE độc lập; Visual Studio có thể mở installer để
  người dùng chọn workload phù hợp.
- Giao diện vẫn giữ hai tab **Phổ thông** và **Chuyên sâu**. Trong Chuyên sâu,
  ứng dụng được chia theo nhu cầu: Lập trình, Marketing & sáng tạo, Văn phòng
  chuyên sâu và Quản trị hệ thống. Một app có thể xuất hiện ở cả Phổ thông lẫn
  nhóm nghề nghiệp phù hợp nhưng dùng chung một trạng thái cài đặt.
- Mỗi card ứng dụng có một câu mô tả ngắn bằng ngôn ngữ phổ thông, giải thích
  trực tiếp ứng dụng dùng để làm gì thay vì chỉ hiển thị tên và publisher.
- Discord được xác minh thêm bằng executable thực tế trong `%LOCALAPPDATA%`, vì
  danh sách Winget tổng có thể trả ID nội bộ `ARP\\User\\X64\\Discord` thay vì
  package ID chuẩn và khiến trạng thái cài đặt bị nhận sai.
- Speedtest qua Ookla CLI và sửa chữa LOW_RISK: flush DNS, release/renew IP.
- Chẩn đoán Windows read-only: pin, ổ đĩa, audio/camera/microphone/Bluetooth,
  máy in, Windows Update, ngày giờ, timezone và startup apps.
- Offline eval cho intent/diagnostics/safety; security headers, JSON rotating log
  và Windows CI cho test, coverage, lint, type check, dependency audit.
- Theo dõi cài/gỡ ứng dụng từ Windows Registry và cập nhật tab Tiện ích qua SSE.
- Tab **Cập nhật WinAssist** hiển thị trạng thái cập nhật và nội dung phiên bản.
- Patch Notes chỉ dùng câu ngắn, dễ hiểu và tránh thuật ngữ kỹ thuật.
- Tab **Hỗ trợ** có form chọn lỗi, mô tả và đính kèm ảnh. Cloudflare Worker gửi
  báo cáo về email hỗ trợ và chỉ trả mã `Ticket#...` sau khi email được chấp nhận.
  Người dùng không cần mở Gmail hoặc GitHub.
- Bộ chuyển ngôn ngữ `VI / EN` nằm trên thanh đầu trang và ghi nhớ lựa chọn trên
  máy cho những lần mở WinAssist tiếp theo.
- Tab **Trợ lý** là lối vào phụ cho người dùng chưa biết cần mở công cụ nào;
  các chức năng chính vẫn có thể dùng trực tiếp qua từng tab.
- Trợ lý hiểu các mô tả phổ thông như máy chậm, máy đơ, máy nóng hoặc mở ứng
  dụng lâu và trả về suggestion có thể bấm để làm rõ triệu chứng.
- Desktop shell dùng WebView2, single-instance, backend lifecycle và local API
  token; dữ liệu runtime nằm trong `%LOCALAPPDATA%\WinAssist Local`.
- Khi khởi động, cửa sổ được căn giữa theo vùng làm việc của monitor đang dùng,
  tự trừ taskbar và thu nhỏ vừa màn hình nếu độ phân giải thấp.
- Khi bấm nút X, WinAssist mở popup giữa ứng dụng với lựa chọn có dấu tick:
  **Thu nhỏ xuống khay** hoặc **Thoát hoàn toàn**, sau đó mới xác nhận. Menu Thoát
  trong system tray đóng ngay và dừng backend, không hỏi lặp.
- PyInstaller onedir build đã sẵn sàng. Ký số và kiểm thử installer trên máy
  Windows sạch vẫn là điều kiện bắt buộc trước khi phát hành Beta công khai.

Hiện tại project tiếp tục mở rộng danh sách **Tiện ích** và tinh chỉnh trải
nghiệm Windows Beta. Onboarding tự quét cấu hình, cài Ollama và chọn model Qwen
được hoãn sang **Giai đoạn 10**; bản hiện tại vẫn fallback an toàn sang
rule-based router khi AI local chưa khả dụng.

Kế hoạch phát triển nằm tại [docs/ROADMAP.md](docs/ROADMAP.md).
Quy trình phát hành GitHub/public domain nằm tại
[docs/DISTRIBUTION.md](docs/DISTRIBUTION.md).

## Quy ước cập nhật tài liệu

- Mỗi thay đổi code phải cập nhật ngắn gọn README và ROADMAP trong cùng lượt.
- `data/processed/patch_notes.json` chỉ cập nhật cho tính năng lớn, thay đổi hành
  vi đáng kể, breaking change hoặc phiên bản phát hành mới.
- Chỉnh sửa nhỏ về khoảng cách, màu sắc, câu chữ hoặc icon không tạo Patch Note.

## Cấu trúc

```text
app/                              Code ứng dụng FastAPI
├── api/                          Khai báo các HTTP endpoint
│   ├── chat.py                   Nhận tin nhắn và gọi AssistantAgent
│   ├── diagnostics.py            API kiểm tra mạng, ping và speedtest
│   ├── software.py               API kiểm tra/cài/gỡ app
│   ├── actions.py                API chạy nền, status, confirm/cancel
│   ├── repairs.py                API chuẩn bị sửa chữa mạng LOW_RISK
│   ├── system.py                 API đọc thông số máy ở chế độ read-only
│   ├── windows.py                API chẩn đoán Windows phổ thông
│   ├── patches.py                API phiên bản cho tab Cập nhật WinAssist
│   └── health.py                 Kiểm tra backend và Ollama
├── core/                         Logic an toàn, không phụ thuộc giao diện
│   ├── command_registry.py       Danh sách command duy nhất được phép chạy
│   ├── command_runner.py         Nơi duy nhất gọi subprocess
│   ├── risk_policy.py            Chặn/cho phép theo mức rủi ro
│   ├── intent_router.py          Phân loại intent bằng rule
│   ├── text_normalization.py     Chuẩn hóa tiếng Việt có/không dấu
│   └── redaction.py              Che MAC, username và secret trước khi lưu
├── services/                     Nghiệp vụ phần mềm, mạng và Ollama
│   ├── network_service.py        Điều phối các bước chẩn đoán mạng
│   ├── software_service.py       Kiểm tra app và tạo pending install
│   ├── action_service.py         Quản lý background action và trạng thái
│   ├── repair_service.py         Chuẩn bị lệnh sửa chữa đã đăng ký
│   ├── speedtest_service.py      Provider và parser Ookla Speedtest
│   ├── system_service.py         Chuẩn hóa CPU, RAM, GPU, OS và ổ hệ thống
│   ├── windows_support_service.py Điều phối capability Windows read-only
│   ├── software_change_watcher.py Theo dõi cài/gỡ ngoài app qua Registry
│   ├── software_catalog.py       Đọc/validate catalog phần mềm
│   ├── ollama_service.py         Gọi Ollama và kiểm tra JSON schema
│   └── prompt_service.py         Đọc prompt có version
├── parsers/                      Chuyển output Windows thành dữ liệu chuẩn
├── models/                       Pydantic schema cho API và nội bộ
├── database/                     SQLite schema và repositories
├── static/                       Frontend app, API client và local state
├── config.py                     Cấu hình từ biến môi trường
├── desktop.py                    Desktop shell, mutex và embedded backend
└── main.py                       Khởi tạo FastAPI và đăng ký router

agents/
└── assistant_agent.py            Điều phối intent và services; không chạy shell

prompts/
├── system/                       Quy tắc vai trò và an toàn của AI
├── tasks/                        Prompt phân loại/tác vụ cụ thể
└── tool_results/                 Prompt giải thích kết quả diagnostics

data/
├── raw/                          Dữ liệu nguồn chưa xử lý
├── processed/                    Catalog, intent examples, patch notes đã duyệt
└── winassist.db                  SQLite sinh lúc chạy, không commit lên Git

tests/                            Unit/integration test bằng mock và fixture
evals/                            Đánh giá chất lượng intent/AI/safety
docs/                             Roadmap và tài liệu kiến trúc
.github/workflows/ci.yml          Quality gate chạy trên Windows
run.ps1                           Script khởi động ứng dụng trên Windows
run-desktop.ps1                   Chạy ứng dụng trong cửa sổ WebView2
build-windows.ps1                 Build Windows Beta bằng PyInstaller
build-installer.ps1               Build installer Beta bằng Inno Setup 6
packaging/WinAssist.spec          Cấu hình bundle executable onedir
packaging/WinAssist.iss           Cấu hình install/upgrade/uninstall per-user
requirements.txt                  Dependency Python
requirements-desktop.txt          Dependency desktop shell và build
.env.example                      Mẫu biến môi trường, không chứa secret thật
```

Trong MVP chỉ có một `AssistantAgent`. Agent không được tạo hoặc chạy shell
command. Command execution luôn thuộc:

- `app/core/command_registry.py`
- `app/core/command_runner.py`
- `app/core/risk_policy.py`

Quy tắc kiểm soát nhanh: API chỉ nhận request, service chứa nghiệp vụ, parser chỉ
đọc output, agent chỉ điều phối, và mọi command hệ thống phải đi qua `core/`.

## Nguyên tắc an toàn

- Không đưa nội dung người dùng trực tiếp vào shell.
- Chỉ chạy command đã định nghĩa trong registry.
- Không tự yêu cầu quyền Administrator.
- `READ_ONLY`: có thể chạy ngay.
- `LOW_RISK`: phải xem trước và xác nhận.
- `HIGH_RISK`: chỉ hướng dẫn thủ công trong MVP.
- Không tắt Defender/Firewall, sửa Registry, gỡ driver hoặc tải installer từ URL
  không xác định.
- Không để LLM tự tạo command hoặc tự xác nhận hành động.
- Mask dữ liệu nhạy cảm trước khi lưu.

## Yêu cầu

- Windows 10/11.
- Python 3.11 trở lên.
- PowerShell 5.1 trở lên.
- Ollama là tùy chọn; khi không có Ollama, ứng dụng dùng rule-based router.

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Nếu PowerShell chặn activation, dùng trực tiếp
`.\.venv\Scripts\python.exe` thay cho `python`.

## Chạy

```powershell
.\run.ps1
```

Mở:

- Ứng dụng: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

## Chạy Windows Desktop Beta

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\run-desktop.ps1
```

Desktop shell dùng WebView2 qua pywebview, chỉ bind backend vào `127.0.0.1` và
tự dừng backend khi đóng cửa sổ. Mỗi lần mở app có token phiên ngẫu nhiên lưu
trong cookie `HttpOnly`; API (trừ health check) từ chối request không thuộc phiên.
Chỉ một desktop instance được chạy cùng lúc.

Launcher `run-desktop.ps1` dùng `pythonw.exe` để không hiện cảnh báo runtime trong
terminal. Log kỹ thuật được lưu tại `%LOCALAPPDATA%\WinAssist Local\data\logs\`
(`desktop-stdout.log` và `desktop-stderr.log`).

Cầu nối pywebview chỉ công khai các thao tác desktop cần thiết; đối tượng cửa sổ
native được giữ nội bộ để tránh lỗi đệ quy `FontFamily/SyncRoot` khi khởi động.
Popup đóng được mở sau khi callback native đã trả về, nên giao diện vẫn nhận click
và không bị treo trong lúc người dùng chọn cách đóng.

Desktop dùng `/api/ready` để xác nhận FastAPI đã mở, không dùng health check đầy
đủ vì kiểm tra Ollama có thể mất vài giây.

Dữ liệu ghi lúc chạy không nằm trong thư mục cài đặt:

```text
%LOCALAPPDATA%\WinAssist Local\data\winassist.db
%LOCALAPPDATA%\WinAssist Local\data\logs\winassist.jsonl
```

## Build Windows Beta

```powershell
.\build-windows.ps1
```

Kết quả nằm tại `dist\WinAssist\WinAssist.exe`. Đây là build Beta chưa ký số;
không phát hành công khai trước khi có certificate, ký binary và kiểm thử trên
Windows 10/11 sạch. Chi tiết tại [docs/WINDOWS_BETA.md](docs/WINDOWS_BETA.md).
Spec resolve asset từ project root để build ổn định dù file nằm trong
`packaging/`. Build onedir `0.9.7` được tạo bằng PyInstaller 6.21.0
trên Windows 11/Python 3.14; GUI vẫn cần smoke test thủ công trên máy sạch.

Installer nội bộ:

```powershell
.\build-installer.ps1
```

Script yêu cầu Inno Setup 6 và tạo installer per-user trong `dist\installer`.
Máy phát triển hiện chưa có `ISCC.exe`, nên installer chưa được build/xác minh.

## Chạy test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Unit test chẩn đoán dùng mock/fixture, không phụ thuộc mạng thật hoặc trạng thái
máy phát triển.

## Diagnostics API

Chạy bộ kiểm tra mạng read-only:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/diagnostics/network
```

Kiểm tra ping với target trong whitelist:

```powershell
$body = @{ target = "1.1.1.1" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/diagnostics/ping `
  -ContentType "application/json" `
  -Body $body
```

Target hợp lệ: `127.0.0.1`, `default_gateway`, `1.1.1.1`, `8.8.8.8` và
`google.com`. Default gateway được đọc từ `ipconfig` rồi xác thực bằng
`ipaddress`; API không nhận hostname hoặc argument tùy ý khác.

Quét các capability Windows phổ thông:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/windows/overview |
  ConvertTo-Json -Depth 10
```

Hoặc kiểm tra riêng: `battery`, `storage`, `devices`, `printers`, `update`,
`datetime`, `startup` qua `POST /api/windows/{capability}`.

Theo dõi thay đổi phần mềm từ Windows:

```text
GET /api/software/events
```

Endpoint dùng Server-Sent Events. Khi danh sách Add/Remove Programs thay đổi,
frontend nhận `software_inventory_changed`, debounce rồi quét lại catalog một
lần. Watcher chỉ đọc Registry. Ứng dụng portable hoặc installer không đăng ký
với Windows vẫn cần nút **Quét lại** để xác minh.

Nội dung bản cập nhật mới nhất:

```text
GET /api/patches/latest
```

## Software API

Xem catalog:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/software
```

Kiểm tra Firefox:

```powershell
$body = @{ software_id = "firefox" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/software/check `
  -ContentType "application/json" -Body $body
```

Tạo pending action cài đặt:

```powershell
$pending = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/software/install `
  -ContentType "application/json" -Body $body
$pending.pending_action
```

Command chưa chạy ở bước trên. Sau khi kiểm tra `display_command`, xác nhận bằng
UUID do backend trả về:

```powershell
$actionId = $pending.pending_action.id
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/actions/$actionId/confirm"
```

Confirm trả về ngay với trạng thái `executing`. Theo dõi tiến trình:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/actions/$actionId/status"
```

Chỉ có thể hủy khi action còn `pending`:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/actions/$actionId/cancel"
```

Catalog hiện có: `firefox`, `7zip`, `vlc`, `libreoffice`, `vscode`, `git`,
`python`, `nodejs`, `ollama` và `speedtest`.

## Chức năng Giai đoạn 6

- Mở **Tiện ích** để cài/gỡ app; luôn kiểm tra command preview trước khi xác nhận.
- Tiện ích có hai nhóm **Phổ thông** và **Chuyên sâu**, sau đó chia tiếp theo
  trình duyệt, văn phòng, media, tiện ích hệ thống và công cụ phát triển.
- Tiện ích quét toàn bộ ứng dụng trong catalog trước khi hiển thị, đánh dấu
  **Đã cài/Chưa cài** và tự quét lại sau khi install/uninstall hoàn tất.
- Inventory được giữ khi đổi tab. Nếu ứng dụng được cài/gỡ từ Control Panel hoặc
  installer bên ngoài, Registry watcher gửi sự kiện SSE để cập nhật gần realtime.
- Với installer có popup ngoài như Firefox, exit code winget không đủ để kết
  luận. WinAssist kiểm tra executable thực tế; nếu người dùng hủy popup thì
  action chuyển `failed` và status vẫn là **Chưa cài**.
- Firefox sử dụng Mozilla uninstaller đã xác minh trong thư mục cài đặt. Nếu
  uninstaller bị hủy hoặc executable vẫn còn, app giữ status **Đã cài** và báo lỗi.
- Nút hủy vẫn hoạt động khi installer đang chạy. Action chuyển sang
  `cancelling`, command runner dừng cây tiến trình đã khởi tạo rồi frontend quét
  lại trạng thái thực tế. Việc hủy giữa chừng có thể để lại thành phần cài dở;
  WinAssist không tự xóa file hoặc Registry để “dọn” cưỡng bức.
- Mở **Chẩn đoán** để kiểm tra mạng, đo tốc độ hoặc chuẩn bị flush DNS,
  release/renew IP.
- Kết quả quét Windows được giải thích bằng thẻ tiếng Việt dễ hiểu; dữ liệu kỹ
  thuật chi tiết vẫn có thể mở xem khi cần.
- Thẻ nội dung ưu tiên tiêu đề và trạng thái; chỉ giữ icon cho điều hướng hoặc
  hành động để giao diện gọn và ít gây rối mắt.
- Mở **Hoạt động** để theo dõi action. Refresh trang không làm mất action đang chạy.
- Speedtest chưa cài sẽ hiện nút **Cài Speedtest để đo**. App vẫn hiển thị
  command preview và yêu cầu xác nhận trước khi cài `Ookla.Speedtest.CLI`.
- Intent rõ ràng được rule-based router xử lý ngay; Ollama chỉ được gọi cho câu
  mơ hồ. Timeout Ollama mặc định là 3 giây để tránh giữ giao diện quá lâu.
- Yêu cầu chung chung không tự chạy command hoặc quét tùy tiện. Trợ lý hiển thị
  các lựa chọn điều hướng như kiểm tra startup, dung lượng, mạng hoặc mở tab
  Chẩn đoán; người dùng chọn bước tiếp theo.

## Chat API

```powershell
$body = @{ message = "Tôi muốn cài Firefox" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/chat `
  -ContentType "application/json" `
  -Body $body |
  ConvertTo-Json -Depth 10
```

Khi Ollama hoặc model không khả dụng, response có warning và
`router_source = "rule_based"`; diagnostics vẫn hoạt động.

## Ollama

`run.ps1` quản lý Ollama theo biến `WINASSIST_OLLAMA_BOOTSTRAP`:

- `prompt` (mặc định): hỏi trước khi cài Ollama hoặc tải model.
- `auto`: tự cài package chính xác bằng winget và tự tải model. Việc đặt giá trị
  này trong `.env` được xem là xác nhận trước của người dùng.
- `skip`: không kiểm tra/cài/khởi động Ollama; app dùng rule-based router.

Nếu Ollama đã được cài nhưng chưa chạy, script tự khởi động `ollama serve` ở cửa
sổ ẩn. Nếu bootstrap thất bại, FastAPI vẫn chạy và tự fallback.

Để bật chế độ tự động, thêm vào `.env`:

```env
WINASSIST_OLLAMA_BOOTSTRAP=auto
WINASSIST_OLLAMA_MODEL=auto
```

Khi model là `auto`, WinAssist chọn theo tổng RAM để ưu tiên phản hồi nhanh:

| RAM | Model |
|---|---|
| Dưới 8 GB | `qwen3:0.6b` |
| 8–15 GB | `qwen3:1.7b` |
| Từ 16 GB | `qwen3:4b` |

Thinking mode được tắt cho tác vụ intent/tóm tắt nhằm giảm độ trễ. Người dùng
nâng cao vẫn có thể đặt tên model cụ thể bằng `WINASSIST_OLLAMA_MODEL`.

## Lỗi thường gặp

- Không nhận `python`: thử `py --version`, kiểm tra PATH và mở terminal mới.
- Thiếu `.venv`: chạy lại phần Cài đặt.
- Port 8000 đang bận: chạy uvicorn với `--port 8001`.
- Không mở được giao diện: kiểm tra uvicorn còn chạy và dùng đúng địa chỉ.
- Cập nhật WinAssist báo backend cũ/Not Found: dừng tiến trình uvicorn hiện tại, chạy
  lại `run.ps1`, sau đó nhấn `Ctrl + F5`.
- `run.ps1` tự thay thế uvicorn cũ nếu process đó thuộc đúng thư mục WinAssist
  hiện tại. Script không dừng process khác đang dùng port 8000.
- Nếu tab mới chưa xuất hiện, tải lại trang. HTML dùng `no-cache`, asset frontend
  có version query và sidebar tự cuộn khi cửa sổ thấp.

## Quality và security

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe evals\run_evals.py
```

Log request được lưu dạng JSON có rotation tại `data/logs/winassist.jsonl`.
Log không chứa request body, query string, nội dung chat hoặc command output.
Threat model nằm tại [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
