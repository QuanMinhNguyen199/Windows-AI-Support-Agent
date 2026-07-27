# WinAssist Local

WinAssist Local là trợ lý hỗ trợ Windows chạy trên máy người dùng. Ứng dụng hướng
tới hai nhóm nhu cầu:

- Người dùng phổ thông: cài ứng dụng cơ bản, kiểm tra Wi-Fi, DNS, âm thanh,
  camera, Bluetooth, máy in, dung lượng và Windows Update.
- Người dùng kỹ thuật: kiểm tra/cài VS Code, Git, Python, Node.js và Ollama.

Ứng dụng ưu tiên kiểm tra read-only. Mọi hành động thay đổi hệ thống phải được
hiển thị trước và chỉ chạy sau khi người dùng xác nhận.

## Trạng thái hiện tại

Project đã hoàn thành **Giai đoạn 1–3**:

- FastAPI server.
- Giao diện chatbot HTML/CSS/JavaScript.
- `GET /api/health`.
- Safety core gồm command registry, risk policy và command runner.
- Chẩn đoán IP, gateway, ping, packet loss, DNS và Wi-Fi.
- `POST /api/diagnostics/network` và `POST /api/diagnostics/ping`.
- Cấu hình qua biến môi trường `WINASSIST_*`.
- Unit/integration test dùng fixture và mock, không chạy mạng thật.

Chat API, software catalog, SQLite, pending action và Ollama chưa được triển
khai. Giao diện chat chưa nối với diagnostics API; API đã có thể gọi trực tiếp.

Kế hoạch phát triển nằm tại [docs/ROADMAP.md](docs/ROADMAP.md).

## Cấu trúc

```text
app/                 FastAPI, API, services, parsers, models, database
prompts/             system prompt, task prompt, prompt giải thích kết quả
data/raw/             dữ liệu nguồn chưa xử lý
data/processed/       catalog phần mềm, intent và troubleshooting rules
agents/               AssistantAgent điều phối AI
evals/                đánh giá intent, chẩn đoán và safety
tests/                unit test và integration test
docs/                 tài liệu kiến trúc và roadmap
```

Trong MVP chỉ có một `AssistantAgent`. Agent không được tạo hoặc chạy shell
command. Command execution luôn thuộc:

- `app/core/command_registry.py`
- `app/core/command_runner.py`
- `app/core/risk_policy.py`

Các file trên là kiến trúc đích và sẽ chỉ được tạo khi đến giai đoạn triển khai.

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
- Ollama là tùy chọn; khi không có Ollama, ứng dụng tương lai sẽ dùng router
  rule-based.

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

## Chuẩn bị Ollama

Ollama chỉ được tích hợp ở giai đoạn AI:

```powershell
ollama pull qwen2.5:3b
ollama serve
```

Có thể đổi model bằng `WINASSIST_OLLAMA_MODEL` trong `.env`.

## Lỗi thường gặp

- Không nhận `python`: thử `py --version`, kiểm tra PATH và mở terminal mới.
- Thiếu `.venv`: chạy lại phần Cài đặt.
- Port 8000 đang bận: chạy uvicorn với `--port 8001`.
- Không mở được giao diện: kiểm tra uvicorn còn chạy và dùng đúng địa chỉ.
