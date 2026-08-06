# Danh mục tiện ích dự kiến

Tài liệu này là backlog mở rộng tab **Tiện ích** sau bản `0.9.9`. Đây không phải
cam kết tất cả ứng dụng sẽ được thêm. Trước khi xuất hiện trong WinAssist, từng
ứng dụng phải được kiểm tra package ID, nhà phát hành, cách nhận diện cài đặt,
gỡ cài đặt và hành vi của installer trên Windows 10/11.

Catalog hiện tại đã có 79 ứng dụng. Danh sách dưới đây chỉ ghi các ứng dụng
**chưa có**, chia thành hai section đúng với giao diện: **Phổ thông** và
**Chuyên sâu**.

## Ưu tiên cho người dùng Việt Nam

Đợt local hiện tại đã đưa **Zalo, Cốc Cốc và UniKey** vào nhóm Phổ thông, đồng
thời thêm CapCut, Figma, Foxit Reader, Bitwarden, ShareX, Obsidian, TreeSize và
CrystalDiskInfo. Đây là các nhu cầu thường gặp khi người Việt mua máy mới hoặc
cài lại Windows: gõ tiếng Việt, liên lạc, duyệt web, học tập, làm nội dung và
kiểm tra dung lượng máy.

Các sản phẩm Việt Nam chỉ có bản web như MISA AMIS, KiotViet, phần mềm ngân
hàng hoặc dịch vụ công sẽ không được giả thành ứng dụng desktop. WinAssist chỉ
tạo lối tắt/mở trang chính hãng nếu sau này có chức năng web app rõ ràng.

## Cách đọc danh sách

- **P1:** nhu cầu phổ biến, nguồn cài rõ và nên xem xét trước.
- **P2:** hữu ích cho một nhóm người dùng cụ thể.
- **P3:** app lớn, trả phí hoặc installer phức tạp; cần thử nghiệm kỹ.
- **WinGet/Store:** mục tiêu là cài trực tiếp trong WinAssist sau xác nhận.
- **Official hub:** WinAssist chỉ cài/mở công cụ chính hãng của nhà phát hành;
  người dùng tự đăng nhập, chọn license và nội dung bên trong công cụ đó.
- **Mở trang chính hãng:** phương án cuối khi không có gói cài tự động đáng tin.

## 1. Phổ thông

### Liên lạc và mạng xã hội

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | WhatsApp | Nhắn tin và gọi điện bằng tài khoản WhatsApp. | Store/WinGet |
| P1 | Slack | Nhắn tin và làm việc theo nhóm. | WinGet |
| P2 | LINE | Nhắn tin, gọi điện và trao đổi file. | WinGet |
| P2 | Viber | Nhắn tin và gọi điện qua Internet. | WinGet |

### Bảo mật và tài khoản

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Proton Pass | Quản lý mật khẩu và thông tin đăng nhập. | WinGet |
| P2 | KeePassXC | Giữ kho mật khẩu trong file trên máy. | WinGet |
| P2 | Malwarebytes | Quét thêm phần mềm độc hại khi cần. | WinGet, không tự chạy quét |
| P2 | Proton VPN | Kết nối VPN bằng tài khoản của người dùng. | WinGet |

### Ảnh, quay màn hình và file media

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Cách tích hợp dự kiến |
|---|---|---|---|
| P2 | GIMP | Chỉnh sửa ảnh miễn phí với nhiều công cụ. | WinGet |
| P2 | Greenshot | Chụp và ghi chú nhanh lên màn hình. | WinGet |
| P2 | ImageGlass | Xem ảnh nhanh với nhiều định dạng. | WinGet |
| P2 | MusicBee | Nghe và quản lý thư viện nhạc trên máy. | WinGet |
| P2 | Plex | Xem thư viện phim và nhạc cá nhân. | WinGet |

### Học tập mở rộng

Anki, Zotero, GeoGebra, draw.io và Calibre đã được chuyển vào catalog thật dưới
section **Học tập cho sinh viên**. Danh sách dưới đây chỉ còn ứng dụng chưa có.

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Package dự kiến |
|---|---|---|---|
| P2 | Microsoft To Do | Tạo danh sách việc cần làm và nhắc lịch. | Store/WinGet |
| P2 | Thunderbird | Đọc nhiều tài khoản email trong một ứng dụng. | WinGet |

### Lưu trữ, tìm file và chăm sóc máy

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | HWiNFO | Xem chi tiết phần cứng và nhiệt độ máy. | WinGet, chỉ đọc |
| P1 | Rufus | Tạo USB cài Windows hoặc hệ điều hành. | WinGet, cảnh báo trước |
| P2 | WinDirStat | Xem dung lượng ổ đĩa bằng bản đồ dễ nhận biết. | WinGet |
| P2 | LocalSend | Chuyển file nhanh giữa các thiết bị cùng mạng. | WinGet |
| P2 | Syncthing | Đồng bộ thư mục giữa các máy của người dùng. | WinGet |
| P2 | Windows PC Manager | Dọn dẹp và kiểm tra máy bằng công cụ Microsoft. | Store/WinGet |

### Giải trí và game

| Ưu tiên | Ứng dụng | Mô tả dễ hiểu | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Xbox | Cài và quản lý game từ hệ sinh thái Xbox/Game Pass. | Store |
| P1 | Battle.net | Cài và mở game của Blizzard. | WinGet/official hub |
| P1 | NVIDIA GeForce NOW | Chơi game qua dịch vụ đám mây. | WinGet |
| P2 | itch.io | Tìm và cài game độc lập. | WinGet |
| P2 | Playnite | Gom thư viện game từ nhiều launcher. | WinGet |
| P2 | Amazon Games | Cài game đi kèm tài khoản Amazon. | Official hub |

## 2. Chuyên sâu

### Văn phòng, quản lý công việc và doanh nghiệp

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | PDFgear | Người cần chỉnh sửa và sắp xếp trang PDF. | Store/WinGet |
| P1 | Todoist | Cá nhân và nhóm quản lý công việc. | WinGet |
| P2 | ClickUp | Nhóm quản lý dự án và đầu việc. | WinGet/web |
| P2 | Trello | Nhóm theo dõi công việc bằng bảng. | Store/web |
| P2 | Miro | Nhóm họp và vẽ bảng ý tưởng trực tuyến. | WinGet |
| P3 | MISA AMIS | Doanh nghiệp Việt Nam dùng hệ sinh thái MISA. | Chỉ nguồn chính hãng |

### Marketing, bán hàng và mạng xã hội

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Microsoft Clipchamp | Người cần dựng video đơn giản trên Windows. | Store |
| P2 | TikTok LIVE Studio | Người phát trực tiếp trên TikTok. | Nguồn chính hãng |
| P2 | Meta Business Suite | Người quản lý Facebook và Instagram. | Web app/PWA, không giả cài desktop |
| P2 | Buffer | Người lên lịch nội dung mạng xã hội. | Web app/PWA |
| P3 | Adobe Creative Cloud | Nhóm dùng Photoshop, Illustrator hoặc Premiere có license. | Official hub |

### Thiết kế, ảnh và sáng tạo nội dung

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Krita | Vẽ minh họa và tranh kỹ thuật số. | WinGet |
| P1 | Inkscape | Thiết kế logo và hình vector miễn phí. | WinGet |
| P1 | DaVinci Resolve | Dựng phim và chỉnh màu chuyên sâu. | WinGet, installer lớn |
| P1 | Kdenlive | Dựng video miễn phí. | WinGet |
| P2 | Shotcut | Cắt ghép video với giao diện gọn. | WinGet |
| P2 | Darktable | Quản lý và chỉnh ảnh RAW. | WinGet |
| P2 | RawTherapee | Chỉnh ảnh chụp định dạng RAW. | WinGet |
| P2 | MuseScore Studio | Viết và nghe bản nhạc. | WinGet |
| P3 | Affinity | Thiết kế ảnh/vector cho người đã mua license. | Store/official hub |

### Dữ liệu, phân tích và nghiên cứu

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Power BI Desktop | Phân tích dữ liệu và làm báo cáo trực quan. | Store/WinGet |
| P1 | R | Phân tích thống kê và nghiên cứu. | WinGet |
| P1 | RStudio Desktop | Viết và chạy dự án phân tích bằng R. | WinGet |
| P1 | JASP | Phân tích thống kê bằng giao diện dễ dùng. | WinGet/nguồn chính hãng |
| P2 | Tableau Public | Tạo biểu đồ và portfolio dữ liệu công khai. | WinGet |
| P2 | Orange Data Mining | Phân tích dữ liệu bằng cách kéo thả. | WinGet |
| P2 | KNIME Analytics Platform | Tạo luồng xử lý dữ liệu trực quan. | WinGet |
| P2 | Julia | Tính toán khoa học và dữ liệu. | WinGet |
| P3 | MATLAB | Kỹ thuật và nghiên cứu có license MATLAB. | Official hub |

### Kỹ thuật, kiến trúc và điện tử

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | FreeCAD | Thiết kế mô hình kỹ thuật 3D miễn phí. | WinGet |
| P1 | KiCad | Thiết kế mạch điện tử và PCB. | WinGet |
| P1 | Arduino IDE | Lập trình bo mạch Arduino. | WinGet |
| P1 | Ultimaker Cura | Chuẩn bị mô hình cho máy in 3D. | WinGet |
| P2 | PrusaSlicer | Cắt lớp mô hình cho máy in 3D. | WinGet |
| P2 | QGIS | Làm bản đồ và phân tích dữ liệu địa lý. | WinGet |
| P3 | Autodesk Access | Quản lý ứng dụng Autodesk chính hãng. | Official hub |
| P3 | SketchUp | Thiết kế kiến trúc và mô hình 3D có license. | Official hub |
| P3 | SOLIDWORKS Installation Manager | Cài SOLIDWORKS bằng license của người dùng. | Official hub, không cung cấp bộ cài lậu |

### Lập trình và phát triển sản phẩm

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | PyCharm Community | Lập trình Python bằng IDE đầy đủ. | WinGet |
| P1 | IntelliJ IDEA Community | Lập trình Java và Kotlin. | WinGet |
| P1 | Android Studio | Phát triển ứng dụng Android. | WinGet, installer lớn |
| P1 | .NET SDK | Xây dựng ứng dụng bằng C# và .NET. | WinGet |
| P1 | Go | Phát triển phần mềm bằng ngôn ngữ Go. | WinGet |
| P1 | Rustup | Cài và quản lý bộ công cụ Rust. | WinGet |
| P2 | Unity Hub | Quản lý Unity Editor và dự án game. | WinGet/official hub |
| P2 | GitKraken | Làm việc với Git bằng giao diện trực quan. | WinGet |
| P2 | Insomnia | Kiểm tra và làm việc với API. | WinGet |
| P2 | MongoDB Compass | Xem và quản lý cơ sở dữ liệu MongoDB. | WinGet |
| P2 | SQL Server Management Studio | Quản lý cơ sở dữ liệu Microsoft SQL Server. | Nguồn Microsoft chính hãng |
| P3 | WSL | Chạy môi trường Linux trong Windows. | Windows feature, cần quyền admin |
| P3 | Unreal Engine | Phát triển game 3D bằng Epic Games Launcher. | Official hub, tải rất lớn |

### Quản trị hệ thống, mạng và hỗ trợ kỹ thuật

| Ưu tiên | Ứng dụng | Dành cho ai? | Cách tích hợp dự kiến |
|---|---|---|---|
| P1 | Sysinternals Suite | Kiểm tra tiến trình, khởi động và hệ thống Windows. | WinGet, công cụ nâng cao |
| P1 | Nmap | Kiểm tra thiết bị và dịch vụ trong mạng được phép. | WinGet, cảnh báo phạm vi sử dụng |
| P1 | Advanced IP Scanner | Tìm thiết bị trong mạng nội bộ. | WinGet/nguồn chính hãng |
| P2 | mRemoteNG | Quản lý nhiều kết nối máy chủ từ xa. | WinGet |
| P2 | Termius | Kết nối SSH và quản lý máy chủ. | WinGet |
| P2 | Tailscale | Kết nối các thiết bị qua mạng riêng an toàn. | WinGet |
| P2 | Ventoy | Tạo USB chứa nhiều bộ cài hệ điều hành. | WinGet, cảnh báo ghi đè USB |
| P3 | VMware Workstation | Chạy máy ảo cho học tập và kiểm thử. | WinGet, cần kiểm tra license |

## Không đưa vào catalog tự động

- Phần mềm crack, key lậu, công cụ bẻ khóa hoặc bộ cài đã bị chỉnh sửa.
- App giả mạo, package không xác minh được publisher hoặc nguồn tải.
- Công cụ tối ưu registry/driver kiểu “một nút sửa tất cả” không có cơ chế
  rollback rõ ràng.
- Trình điều khiển lấy từ website tổng hợp; driver chỉ lấy từ Windows Update,
  hãng sản xuất thiết bị hoặc nhà sản xuất phần cứng.
- App điều khiển từ xa như AnyDesk/TeamViewer trong danh sách phổ thông. Nếu bổ
  sung cho hỗ trợ kỹ thuật, phải cảnh báo lừa đảo và không tự bật unattended access.
- Web service không có desktop app thật. WinAssist có thể tạo shortcut/PWA nhưng
  phải ghi đúng là “Mở web”, không được giả là đã cài ứng dụng desktop.

## Quy trình đưa một app vào WinAssist

1. Xác nhận nhu cầu và bảo đảm chưa trùng chức năng quá nhiều với app hiện có.
2. Chạy `winget search`, sau đó `winget show` để kiểm tra đúng package ID,
   publisher, installer, kiến trúc máy và nguồn.
3. Ưu tiên source mặc định `winget` hoặc `msstore`; không thêm repository lạ.
4. Thêm command cài, gỡ và xác minh vào Safety Core; agent chỉ điều phối.
5. Kiểm thử cài, người dùng hủy installer, gỡ từ WinAssist và gỡ từ bên ngoài.
6. Chỉ báo “Đã cài” sau khi kiểm tra executable/registry/WinGet thực tế.
7. Kiểm tra mô tả, license, dung lượng dự kiến, yêu cầu admin và restart.
8. Thêm unit/integration test trước khi phát hành catalog mới.

Microsoft khuyến nghị dùng package ID chính xác và kiểm tra gói bằng `winget
search/show` trước khi cài. WinGet hỗ trợ nguồn cộng đồng và Microsoft Store,
nhưng hành vi nâng quyền vẫn phụ thuộc từng installer. Tham khảo:
[Microsoft Learn — WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
và [winget-pkgs](https://github.com/microsoft/winget-pkgs).

## Thứ tự đề xuất

Đợt tiếp theo chỉ nên thêm khoảng 10–15 app P1, không nhập toàn bộ backlog cùng
lúc. Nhóm đầu nên cân bằng nhiều nhu cầu:

1. WhatsApp, Viber và LINE.
2. Microsoft To Do và Thunderbird.
3. HWiNFO, WinDirStat và LocalSend.
4. Krita, Inkscape và Kdenlive.
5. Power BI Desktop, RStudio và Arduino IDE.
6. MISA chỉ qua nguồn chính hãng, không tự động cấp license.

Sau mỗi đợt cần đo tỷ lệ cài thành công, lỗi hủy, nhận diện app đã có và phản hồi
người dùng trước khi mở rộng tiếp.
