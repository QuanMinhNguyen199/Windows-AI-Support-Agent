# Kết nối hệ thống ticket Beta

Worker nhận ticket tại `https://winassist-support.minhquanpro65.workers.dev/`.
Mã nguồn cần deploy nằm ở `cloudflare/support-worker.js`.

## Thiết lập trên Cloudflare

1. Mở Worker `winassist-support`, chọn **Edit code**.
2. Thay mã mẫu `Hello World` bằng nội dung `cloudflare/support-worker.js`.
3. Chọn **Deploy**.
4. Vào **Settings → Variables and Secrets** và thêm:
   - Secret `RESEND_API_KEY`: API key lấy từ Resend.
   - Variable `SUPPORT_EMAIL`: `minhquanpro65@gmail.com`.
5. Trong bản Beta có thể giữ người gửi mặc định
   `WinAssist Beta <onboarding@resend.dev>`; tài khoản Resend phải đăng ký bằng
   chính email nhận ở trên.

Không đưa `RESEND_API_KEY` vào source code, screenshot, GitHub hoặc file `.env`.

## Giới hạn an toàn

- Chỉ nhận request từ app local và trang GitHub Pages chính thức.
- Chỉ nhận PNG, JPG hoặc WebP, tối đa 5 MB.
- Nội dung mô tả từ 10 đến 4.000 ký tự.
- Email chỉ được đánh dấu gửi thành công khi Resend trả về thành công.
- Email liên hệ là tùy chọn và chỉ được nhận khi người dùng tick đồng ý phản hồi.
- Khi có email liên hệ, Worker đặt `reply_to` để nút Reply trong Gmail gửi đúng
  tới người báo lỗi, không gửi ngược về địa chỉ Resend.
- Thông tin action đính kèm chỉ gồm ID, loại thao tác, package, exit code,
  timeout và phần giải thích đã giới hạn; không nhận stdout/stderr thô.
