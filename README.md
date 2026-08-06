# WinAssist

WinAssist là ứng dụng hỗ trợ máy tính Windows dành cho người dùng phổ thông.
Ứng dụng giúp bạn xem tình trạng máy, chẩn đoán lỗi thường gặp, cài tiện ích và
theo dõi cập nhật trong một giao diện đơn giản.

> **Tải Community Beta:** [Tải WinAssist cho Windows](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest/download/WinAssist-Setup.exe)
>
> Không cần cài Python hay mở terminal. Bản Beta chưa ký số nên Windows
> SmartScreen có thể hiện cảnh báo. Chỉ tải từ [website chính thức](https://quanminhnguyen199.github.io/Windows-AI-Support-Agent/)
> hoặc GitHub của dự án.

## WinAssist có thể làm gì?

- Hiển thị nhanh Windows, CPU, RAM, card màn hình và dung lượng ổ đĩa.
- Kiểm tra mạng, Wi-Fi, DNS, ping và tốc độ kết nối.
- Kiểm tra pin, âm thanh, camera, Bluetooth, máy in và ứng dụng khởi động.
- Cài hoặc gỡ các ứng dụng phổ biến bằng danh mục đã được kiểm duyệt.
- Kiểm tra card màn hình, Windows Update và phiên bản mới của WinAssist.
- Hỗ trợ tiếng Việt và tiếng Anh.
- Trợ lý gợi ý nhanh các ứng dụng cơ bản; nhấn `Enter` để gửi và
  `Shift+Enter` để xuống dòng.
- Gửi báo cáo lỗi kèm ảnh ngay trong ứng dụng.

WinAssist ưu tiên kiểm tra mà không thay đổi máy. Trước mọi thao tác cài đặt,
gỡ ứng dụng hoặc thay đổi hệ thống, ứng dụng sẽ cho bạn xem và xác nhận.

## Phiên bản hiện tại

**WinAssist 0.10.1 Community Beta** bổ sung cập nhật ngay trong ứng dụng với
tiến trình tải, hủy và kiểm tra SHA-256 trước khi cài.

- [Tải bản mới nhất](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest/download/WinAssist-Setup.exe)
- [Xem thay đổi của phiên bản](https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest)
- [Kế hoạch phát triển](docs/ROADMAP.md)

## Công nghệ sử dụng

- **Python + FastAPI:** xử lý API, dịch vụ và chẩn đoán máy.
- **HTML, CSS và JavaScript:** giao diện người dùng.
- **pywebview:** đưa giao diện web vào ứng dụng Windows riêng.
- **SQLite:** lưu trạng thái và lịch sử ngay trên máy.
- **Ollama:** AI local tùy chọn; nếu chưa có, ứng dụng dùng bộ định tuyến theo luật.
- **PyInstaller + Inno Setup:** đóng gói thành bộ cài Windows.
- **GitHub Actions và GitHub Pages:** kiểm thử, phát hành và cung cấp trang tải.

Từ `0.10.0`, WinAssist tải bản mới ở nền, kiểm tra SHA-256 rồi tự đóng, cài và
mở lại. Người dùng `0.9.9` cần cài `0.10.0` thủ công một lần để nhận updater mới.
Hotfix `0.10.1` cũng sửa luồng gỡ cài đặt để không còn sót file đang bị Windows khóa.

Các bản vá nhỏ được gom vào chu kỳ phát triển hiện tại, không tạo Patch Note và
không tăng phiên bản riêng. Chỉ bản có thay đổi đáng kể mới được lập nội dung tại
[`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md), duyệt xong rồi mới phát hành.

Website tải WinAssist có giao diện responsive, hiển thị tính năng, hướng dẫn cài
và ghi chú phiên bản ngay trên trang; người dùng phổ thông không cần mở GitHub.
Số lượt tải trên website được lấy trực tiếp từ GitHub Release, không dùng số liệu
ước tính hoặc social proof giả.

Giao diện desktop giữ nội dung cân giữa, đặt thanh cuộn sát mép cửa sổ và chừa
khoảng cách an toàn để nội dung không dính vào scrollbar.

Logic chạy lệnh hệ thống chỉ được quản lý tại:
`app/core/command_registry.py`, `app/core/command_runner.py` và
`app/core/risk_policy.py`. AI agent không chạy lệnh shell trực tiếp.

## Dành cho người muốn phát triển

Yêu cầu Python 3.11 trở lên:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
.\run.ps1
```

Tài liệu chi tiết:

- [Phân phối và cài đặt](docs/DISTRIBUTION.md)
- [Kiểm thử Windows Beta](docs/WINDOWS_BETA.md)
- [Mô hình an toàn](docs/THREAT_MODEL.md)
- [Roadmap](docs/ROADMAP.md)
- [Danh mục tiện ích dự kiến](docs/FUTURE_APP_CATALOG.md)

## Cấu trúc chính

```text
app/       Ứng dụng FastAPI, API, services, models, database và giao diện
agents/    Lớp điều phối AssistantAgent, không thực thi shell trực tiếp
prompts/   System prompt, task prompt và giải thích kết quả công cụ
data/      Dữ liệu nguồn và dữ liệu đã xử lý
evals/     Đánh giá chất lượng intent, chẩn đoán và an toàn của AI
tests/     Unit test và integration test của code
docs/      Hướng dẫn kỹ thuật và kế hoạch phát triển
packaging/ Cấu hình đóng gói ứng dụng Windows
public/    Website tải WinAssist
```

## Hỗ trợ

Bạn có thể gửi ticket trong tab **Hỗ trợ** của WinAssist hoặc liên hệ
[minhquanpro65@gmail.com](mailto:minhquanpro65@gmail.com).

Dự án đang ở giai đoạn Community Beta và chưa ký số. Không gửi mật khẩu, mã xác
thực hoặc thông tin tài khoản cá nhân trong báo cáo lỗi.
