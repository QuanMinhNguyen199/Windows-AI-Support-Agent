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

- Bản phát hành chính tăng tuần tự: `0.11.1` → `0.11.2` → `0.11.3`.
- Hotfix của một bản giữ ba thành phần chính và thêm số sửa lỗi: `0.11.2.1`,
  `0.11.2.2`...; khi có thay đổi lớn tiếp theo mới chuyển thành `0.11.3`.
- Hotfix không thay đổi tính năng lớn sẽ dùng cùng nhánh release và được updater
  nhận diện như một version mới hơn bản ba thành phần tương ứng.
- Việc ghi thay đổi vào file này không tự tăng version trong code.
- Nhiều bản vá nhỏ có thể được gom chung vào phiên bản kế tiếp đang ở trạng thái nháp.
- Chỉ sau lệnh triển khai mới chốt version, đồng bộ Patch Notes, build, tạo tag
  và phát hành installer.

## Bản kế tiếp — Nháp

### Ý tưởng đang xem xét — chưa triển khai

- Mở rộng Tiện ích theo một đợt nhỏ, ưu tiên ứng dụng có nguồn cài rõ ràng:
  WhatsApp, Viber, Thunderbird, LocalSend, HWiNFO, Rufus, Battle.net, Krita,
  Inkscape, Power BI Desktop, Arduino IDE và Sysinternals Suite.
- Chưa đưa LINE và Windows PC Manager vào đợt đầu cho tới khi xác minh ổn định
  nguồn Store, cách nhận diện đã cài và cách gỡ.
- Không nhập hàng loạt ứng dụng trùng chức năng. WinAssist sẽ xếp app phổ biến
  lên trước và giải thích ngắn app phù hợp với ai.
- Trước khi tăng số lượng app, củng cố kiểm tra dung lượng trống, quyền quản trị,
  nguồn WinGet/Store, trạng thái tải, thao tác hủy và kiểm tra lại sau cài/gỡ.
- Mỗi app mới phải có tên dễ hiểu, dung lượng dự kiến, yêu cầu đăng nhập/bản
  quyền, khả năng cần khởi động lại và hướng xử lý khi cài thất bại.
- Thêm kiểm thử Windows 10/11 cho cài, hủy, gỡ, gỡ sạch dữ liệu tùy chọn và nhận
  diện ứng dụng được cài/gỡ từ bên ngoài WinAssist.
- Mở rộng tab Chuyên sâu theo ba nhu cầu: **Marketing**, **Thiết kế** và **Kế
  toán**; vẫn giữ nguyên hai tab Phổ thông/Chuyên sâu.
- Dự kiến bổ sung Google Ads Editor, Metricool, Krita, Inkscape, MISA SME, HTKK
  và iTaxViewer theo từng đợt kiểm thử, không nhập toàn bộ cùng lúc.
- Bổ sung công cụ AI chính hãng như ChatGPT, Claude Desktop và Microsoft
  Copilot. App phải nói rõ công cụ cần Internet/tài khoản hay tải mô hình về máy.
- Dịch vụ chỉ có trên web như HubSpot, Mailchimp, Adobe Firefly hoặc MISA AMIS
  phải hiển thị là **Mở web**, không giả thành ứng dụng đã cài trên Windows.
- Công cụ kế toán/thuế chỉ dùng nguồn chính hãng, không tự nhập dữ liệu, cài
  driver chữ ký số hoặc kích hoạt bản quyền thay người dùng.

### Checklist của chủ dự án

- [x] Đã chốt danh sách ứng dụng thực sự cần cho đợt này.
- [x] Đã chốt app nào là desktop, Store, web/PWA hoặc official hub.
- [x] Package ID, publisher và nguồn cài của từng app đã được xác minh.
- [x] Cài, hủy, gỡ và nhận diện trạng thái đã được thử trên máy sạch.
- [x] Nội dung hiển thị dùng câu ngắn, dễ hiểu và không hứa quá khả năng.
- [x] Test tự động đã đạt và không còn lỗi chặn phát hành.
- [x] Đã đồng ý version sẽ phát hành.
- [x] Đã đưa ra lệnh triển khai rõ ràng.

## 0.11.3 — Phát hành ngày 08/08/2026

### Có gì mới?

- Cập nhật tự tiếp tục tải phần còn thiếu nếu WinAssist bị đóng giữa chừng.
- Thêm **Rufus**, **Mozilla Thunderbird** và **LocalSend** vào Tiện ích.
- Trợ lý tự nhận Ollama đã có trên máy và chọn thiết lập phù hợp mà không hiện
  tên model cho người dùng phổ thông.

### Đã sửa

- Không còn tải lại bộ cài Ollama khi máy đã có Ollama.
- Nội dung **Dọn dẹp máy** được rút gọn, dễ hiểu hơn.
- Updater hỗ trợ hotfix bốn thành phần như `0.11.3.1`.

**Trạng thái: ĐÃ CHỐT LOCAL** — chờ test, build và phát hành installer `0.11.3`.

## 0.11.3.1 — Hotfix ngày 08/08/2026

### Đã sửa

- Không còn hiển thị cố định `50%` khi đang chuẩn bị trợ lý AI.
- Hiển thị thời gian đã chờ và thông báo rõ khi lần đầu tải trợ lý AI có thể mất
  vài phút.
- Tự thử lại khi Ollama khởi động chậm và báo lỗi rõ nếu quá thời gian.

**Trạng thái: ĐÃ CHỐT LOCAL** — sẵn sàng test, build và phát hành hotfix.

## 0.11.2 — Phát hành ngày 08/08/2026

### Có gì mới?

- Khi mở tab **Trợ lý** trên máy chưa có Local AI, WinAssist hỏi người dùng có
  muốn cài Ollama và model AI hay không. Người dùng có thể từ chối và tiếp tục
  dùng các chức năng khác bình thường.
- Nếu đồng ý, Ollama và model phù hợp với dung lượng RAM được tải và cài ngay
  trong cửa sổ WinAssist, không cần mở trình duyệt hoặc cài thủ công.
- Tab **Tiện ích** có ô tìm kiếm theo tên, nhà phát hành, mô tả hoặc nhu cầu;
  tìm kiếm không phân biệt dấu tiếng Việt và chữ hoa/thường.

### Đã sửa

- Khi lệnh cài ứng dụng trả về thành công nhưng bước xác minh chưa kịp nhận diện,
  Hoạt động giữ trạng thái hoàn tất và chỉ hiển thị cảnh báo chưa xác minh.
- Bổ sung kiểm thử cho trường hợp installer thành công nhưng xác minh sau cài
  chưa có kết quả.

### Checklist phát hành

- [x] Đã chốt danh sách thay đổi.
- [x] Đã kiểm tra test tự động.
- [x] Đã cập nhật nội dung Có gì mới? trên website.
- [x] Đã chốt version `0.11.2`.

**Trạng thái: ĐÃ BUILD LOCAL** — installer `0.11.2` đã được tạo và sẵn sàng để
đưa lên asset public sau khi chủ dự án kiểm tra file cài trên Windows sạch.


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

- [] Tất cả chức năng dự kiến phát hành đã được thử trực tiếp trên bản local.
- [] Đã kiểm tra danh sách thay đổi.
- [] Đã kiểm tra giao diện và hành vi trên Windows.
- [] Các thao tác cài, gỡ, cập nhật và xóa dữ liệu đã cho kết quả đúng.
- [] Patch Note chỉ mô tả điều người dùng sẽ thấy, dùng câu ngắn và không có
      thuật ngữ kỹ thuật khó hiểu.
- [] Toàn bộ test tự động đã đạt và không còn lỗi chặn phát hành.
- [] Đã đồng ý version sẽ phát hành.
- [] Đã đưa ra lệnh triển khai rõ ràng.

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
