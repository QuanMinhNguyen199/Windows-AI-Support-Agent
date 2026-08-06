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
- Có 79 tiện ích, gồm Zalo, Cốc Cốc, UniKey và các công cụ học tập, văn phòng,
  sáng tạo nội dung thường dùng tại Việt Nam.
- Có nhóm học tập riêng với Anki, Zotero, GeoGebra, draw.io và Calibre; mỗi ứng
  dụng được chọn cài riêng để tránh trùng chức năng.
- Quét dung lượng rồi dọn file tạm an toàn theo đúng các mục bạn tự chọn.
  Nếu phép quét lỗi, WinAssist báo để thử lại thay vì hiển thị kết quả trống.
- Kiểm tra card màn hình, Windows Update và phiên bản mới của WinAssist.
- Hỗ trợ tiếng Việt và tiếng Anh.
- Trợ lý gợi ý nhanh các ứng dụng cơ bản; nhấn `Enter` để gửi và
  `Shift+Enter` để xuống dòng.
- Gửi báo cáo lỗi kèm ảnh ngay trong ứng dụng.
- Form hỗ trợ được bố trí gọn trong một màn hình desktop và vẫn thích ứng khi
  cửa sổ hẹp.
- Theo dõi hoạt động bằng tên dễ hiểu; thông tin kỹ thuật được thu gọn để dùng
  khi cần kiểm tra hoặc gửi báo cáo lỗi.
- Hiển thị thanh tiến trình khi đang quét, tải hoặc xử lý; không dùng phần trăm
  giả cho thao tác chưa cung cấp tiến độ chính xác.
- Thanh điều hướng giữ nhãn trên một dòng và đặt thanh cuộn sát cạnh sidebar.

WinAssist ưu tiên kiểm tra mà không thay đổi máy. Trước mọi thao tác cài đặt,
gỡ ứng dụng hoặc thay đổi hệ thống, ứng dụng sẽ cho bạn xem và xác nhận.

## Phiên bản hiện tại

**WinAssist 0.11.1 Community Beta** bổ sung dọn file tạm an toàn, mở rộng kho
Tiện ích và làm rõ kết quả kiểm tra cho người dùng phổ thông. Bản này vẫn giữ
cơ chế cập nhật bắt buộc cho phiên bản cũ; bản mới được tải ngay trong ứng dụng,
có tiến trình, nút hủy và bước kiểm tra SHA-256 trước khi cài.

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

Mọi thay đổi đều được ghi trước tại
[`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md). WinAssist chỉ tạo release mới
sau khi chủ dự án kiểm tra checklist và đưa ra lệnh triển khai rõ ràng.
Khi đã có bản phát hành chính thức mới, phiên bản cũ sẽ yêu cầu cập nhật trước
khi người dùng tiếp tục sử dụng các chức năng khác.

Khi gặp lỗi, WinAssist tự ghi thông tin kỹ thuật đã được rút gọn vào
`%LOCALAPPDATA%\WinAssist Local\data\logs\debug-errors.jsonl`. File này không
ghi các thao tác thành công và không lưu mật khẩu, token hay command arguments.

Website tải WinAssist có giao diện responsive, hiển thị tính năng, hướng dẫn cài
và ghi chú phiên bản theo luồng dễ hiểu; người dùng phổ thông không cần mở GitHub.
Mục **Có gì mới?** hiển thị đúng nội dung của bản `0.11.1` và lấy ngày phát hành
thật từ GitHub Release.
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
