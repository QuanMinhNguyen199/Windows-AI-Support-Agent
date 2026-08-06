# WinAssist — Release Notes

Đây là file duy nhất dùng để chuẩn bị nội dung trước một bản phát hành đáng kể.
Không tạo mục mới cho sửa lỗi nhỏ, chỉnh chữ hoặc tinh chỉnh giao diện. Những
thay đổi nhỏ được gom vào bản lớn tiếp theo.

## 0.11.0 — Chuẩn bị phát hành

### Mục tiêu

Đảm bảo người dùng không tiếp tục chạy phiên bản WinAssist đã lỗi thời.

### Thay đổi người dùng sẽ thấy

- Hiện thông báo bắt buộc ngay khi mở một phiên bản cũ.
- Khóa các chức năng khác cho tới khi cập nhật hoàn tất.
- Bản có updater sẽ tải, kiểm tra và cài ngay trong WinAssist.
- Từ bản chứa cơ chế này, mọi phiên bản cũ hơn bản phát hành chính thức sẽ bị
  khóa cho tới khi cập nhật xong.

### Lỗi quan trọng đã sửa

- Chưa có.

### An toàn và dữ liệu

- Không khóa ứng dụng nếu chưa kiểm tra được phiên bản do mất mạng.
- Chỉ bắt buộc cập nhật khi GitHub đã có bộ cài chính thức.

### Điều kiện phát hành

- [ ] Thay đổi đủ lớn và có ích rõ ràng cho người dùng.
- [ ] Nội dung bên trên ngắn gọn, không dùng thuật ngữ kỹ thuật khó hiểu.
- [x] Unit test và integration test đều đạt.
- [ ] Bộ cài Windows được kiểm thử cài/gỡ trên Windows runner sạch trước khi publish.
- [x] README và ROADMAP đã cập nhật.
- [x] Yêu cầu triển khai đã được xác nhận trong cuộc trao đổi sản phẩm.

## Đã phát hành

### 0.10.0 — Cập nhật ngay trong WinAssist

- Tải và cài phiên bản mới ngay trong ứng dụng.
- Hiển thị tiến trình và cho phép hủy khi đang tải.
- Kiểm tra gói cài đặt chính thức trước khi chạy.

> Bản vá kỹ thuật 0.10.1 sửa lỗi gỡ cài đặt đã được phát hành trước khi quy ước
> này có hiệu lực, nên không được tính là một Patch Note mới.
