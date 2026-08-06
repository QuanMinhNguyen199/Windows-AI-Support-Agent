# WinAssist — Release Notes

Đây là file duy nhất dùng để ghi nhận **mọi thay đổi** trước khi phát hành.
Mỗi thay đổi mới chỉ được thêm vào mục **Bản kế tiếp — Nháp**. Không build
release, tạo tag, tải asset lên GitHub hoặc cập nhật bản public cho đến khi chủ
dự án kiểm tra đủ và đưa ra lệnh triển khai rõ ràng.

> **Cổng phát hành bắt buộc:** Trước mọi thao tác commit bản phát hành, push,
> tạo tag, build bản public hoặc cập nhật GitHub Release, phải đọc lại mục
> **Checklist của chủ dự án** trong file này. Chỉ được triển khai khi toàn bộ
> checkbox trong mục đó là `[x]`. Một lệnh “triển khai” riêng lẻ không thay thế
> checklist còn thiếu. Codex không tự tick thay chủ dự án.

## Quy tắc phiên bản

- Tăng tuần tự: `0.10.1` → `0.10.2` → ... → `0.10.9`.
- Thành phần cuối chỉ từ `0` đến `9`; sau `0.10.9` chuyển sang `0.11.0`.
- Việc ghi thay đổi vào file này không tự tăng version trong code.
- Nhiều bản vá nhỏ có thể được gom chung vào phiên bản kế tiếp đang ở trạng thái nháp.
- Chỉ sau lệnh triển khai mới chốt version, đồng bộ Patch Notes, build, tạo tag
  và phát hành installer.

## 0.11.1 — Phát hành ngày 06/08/2026

### Có gì mới?

- Có mục **Dọn dẹp máy**: xem dung lượng file tạm, tự chọn mục cần dọn rồi xác
  nhận trước khi xóa. WinAssist không đụng vào tài liệu và file cá nhân.
- Kho Tiện ích có thêm ứng dụng quen thuộc tại Việt Nam và nhóm **Học tập cho
  sinh viên**, gồm Anki, Zotero, GeoGebra, draw.io và Calibre.
- Có Microsoft 365 trong nhóm Văn phòng, kèm lưu ý cần tài khoản có bản quyền.
- Có thể tìm và cài Windows Update ngay trong WinAssist. Ứng dụng không tự khởi
  động lại máy.
- Bản cập nhật WinAssist được cài ẩn rồi ứng dụng tự mở lại, không còn yêu cầu
  đi qua Setup Wizard ở mỗi lần cập nhật.

### Đã sửa

- Tab Hoạt động dùng tên và lời giải thích dễ hiểu thay cho lệnh kỹ thuật dài.
- Khi cài hoặc gỡ tiện ích thất bại, WinAssist nói rõ nguyên nhân thường gặp và
  cho phép gửi báo cáo kèm mã lỗi.
- Quét file tạm không còn báo `0` khi Windows thực sự không đọc được thư mục.
- Kết quả mạng hiển thị **Độ trễ** và **Độ dao động**, làm tròn để tránh hiểu
  nhầm con số.
- Thanh điều hướng, thanh cuộn, form Hỗ trợ và trạng thái tải đã được căn gọn hơn.
- Website giới thiệu sản phẩm theo đúng trình tự sử dụng và dùng câu dễ hiểu hơn.
- Website hiển thị đúng nội dung **Có gì mới?** và ngày phát hành của `0.11.1`,
  không còn giữ ba dòng mô tả từ phiên bản trước.
- Bản vá thay thế installer `0.11.1`: cập nhật ẩn luôn tạo lại shortcut WinAssist
  ngoài Desktop, không còn làm mất biểu tượng sau khi nâng cấp.
- Nếu lần kiểm tra phiên bản lúc mở app bị lỗi tạm thời, WinAssist tự thử lại;
  từ `0.11.1`, phiên bản cũ hơn bản mới tiếp theo sẽ hiện cửa sổ cập nhật bắt buộc.

### An toàn và dữ liệu

- Mọi thao tác cài, gỡ, cập nhật hoặc xóa file đều phải được xác nhận trước.
- Nhật ký kiểm tra lỗi chỉ lưu thao tác thất bại, tự che thông tin nhạy cảm và
  không ghi mật khẩu, token hoặc nội dung cá nhân.
- Gỡ sạch tiện ích chỉ dọn cache đã được kiểm duyệt; vẫn giữ tài khoản, cài đặt,
  bookmark, project, game và file cá nhân.

### Checklist của chủ dự án

- [x] Tất cả chức năng dự kiến phát hành đã được thử trực tiếp trên bản local.
- [x] Đã kiểm tra danh sách thay đổi.
- [x] Đã kiểm tra giao diện và hành vi trên Windows.
- [x] Các thao tác cài, gỡ, cập nhật và xóa dữ liệu đã cho kết quả đúng.
- [x] Patch Note chỉ mô tả điều người dùng sẽ thấy, dùng câu ngắn và không có
      thuật ngữ kỹ thuật khó hiểu.
- [x] Toàn bộ test tự động đã đạt và không còn lỗi chặn phát hành.
- [x] Đã đồng ý version sẽ phát hành.
- [x] Đã đưa ra lệnh triển khai rõ ràng.

**Trạng thái: ĐÃ DUYỆT PHÁT HÀNH** — checklist đã đủ và chủ dự án đã yêu cầu
commit, push và tạo bản `0.11.1`.

## 0.11.0 — Đã phát hành ngày 06/08/2026

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

- [x] Thay đổi đủ lớn và có ích rõ ràng cho người dùng.
- [x] Nội dung bên trên ngắn gọn, không dùng thuật ngữ kỹ thuật khó hiểu.
- [x] Unit test và integration test đều đạt.
- [x] Bộ cài Windows đã cài/gỡ sạch trên Windows runner trước khi publish.
- [x] README và ROADMAP đã cập nhật.
- [x] Yêu cầu triển khai đã được xác nhận trong cuộc trao đổi sản phẩm.

## Các bản trước

### 0.10.0 — Cập nhật ngay trong WinAssist

- Tải và cài phiên bản mới ngay trong ứng dụng.
- Hiển thị tiến trình và cho phép hủy khi đang tải.
- Kiểm tra gói cài đặt chính thức trước khi chạy.

> Bản vá kỹ thuật 0.10.1 sửa lỗi gỡ cài đặt đã được phát hành trước khi quy ước
> này có hiệu lực, nên không được tính là một Patch Note mới.
