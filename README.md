# WinAssist Local

WinAssist Local là trợ lý hỗ trợ Windows chạy trên máy người dùng. Ứng dụng hướng
tới hai nhóm nhu cầu:

- Người dùng phổ thông: cài ứng dụng cơ bản, kiểm tra Wi-Fi, DNS, âm thanh,
  camera, Bluetooth, máy in, dung lượng và Windows Update.
- Người dùng kỹ thuật: kiểm tra/cài VS Code, Git, Python, Node.js và Ollama.

Ứng dụng ưu tiên kiểm tra read-only. Mọi hành động thay đổi hệ thống phải được
hiển thị trước và chỉ chạy sau khi người dùng xác nhận.

## Trạng thái hiện tại

Project đã hoàn thành **Giai đoạn 1–6**:

- FastAPI server.
- Giao diện chatbot HTML/CSS/JavaScript.
- `GET /api/health`.
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
- Màn hình Tổng quan máy luôn mở trước, hiển thị Windows, CPU, RAM, GPU và ổ hệ thống.
- Cài/gỡ ứng dụng chạy nền, có command preview, xác nhận, hủy pending action,
  trạng thái và progress không xác định.
- Speedtest qua Ookla CLI và sửa chữa LOW_RISK: flush DNS, release/renew IP.

Kế hoạch phát triển nằm tại [docs/ROADMAP.md](docs/ROADMAP.md).

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
│   ├── software_catalog.py       Đọc/validate catalog phần mềm
│   ├── ollama_service.py         Gọi Ollama và kiểm tra JSON schema
│   └── prompt_service.py         Đọc prompt có version
├── parsers/                      Chuyển output Windows thành dữ liệu chuẩn
├── models/                       Pydantic schema cho API và nội bộ
├── database/                     SQLite schema và repositories
├── static/                       Frontend app, API client và local state
├── config.py                     Cấu hình từ biến môi trường
└── main.py                       Khởi tạo FastAPI và đăng ký router

agents/
└── assistant_agent.py            Điều phối intent và services; không chạy shell

prompts/
├── system/                       Quy tắc vai trò và an toàn của AI
├── tasks/                        Prompt phân loại/tác vụ cụ thể
└── tool_results/                 Prompt giải thích kết quả diagnostics

data/
├── raw/                          Dữ liệu nguồn chưa xử lý
├── processed/                    Catalog, intent examples và rules đã duyệt
└── winassist.db                  SQLite sinh lúc chạy, không commit lên Git

tests/                            Unit/integration test bằng mock và fixture
evals/                            Đánh giá chất lượng intent/AI/safety
docs/                             Roadmap và tài liệu kiến trúc
run.ps1                           Script khởi động ứng dụng trên Windows
requirements.txt                  Dependency Python
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
- Mở **Chẩn đoán** để kiểm tra mạng, đo tốc độ hoặc chuẩn bị flush DNS,
  release/renew IP.
- Mở **Hoạt động** để theo dõi action. Refresh trang không làm mất action đang chạy.
- Speedtest chưa cài sẽ hiện nút **Cài Speedtest để đo**. App vẫn hiển thị
  command preview và yêu cầu xác nhận trước khi cài `Ookla.Speedtest.CLI`.
- Intent rõ ràng được rule-based router xử lý ngay; Ollama chỉ được gọi cho câu
  mơ hồ. Timeout Ollama mặc định là 3 giây để tránh giữ giao diện quá lâu.

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
