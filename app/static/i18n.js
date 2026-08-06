(() => {
  const STORAGE_KEY = "winassist-language";
  const en = {
    "Tổng quan máy": "PC overview", "Trợ lý": "Assistant", "Tiện ích": "Apps",
    "Chẩn đoán": "Diagnostics", "Card màn hình": "Graphics", "Cập nhật Windows": "Windows Update",
    "Hoạt động": "Activity", "Cập nhật WinAssist": "Update WinAssist", "Hỗ trợ": "Support",
    "Gỡ WinAssist": "Uninstall WinAssist", "Đang kết nối…": "Connecting…",
    "Trợ lý: đang chuẩn bị": "Assistant: getting ready", "Hỗ trợ máy tính Windows": "Windows computer support",
    "Dữ liệu được giữ trên máy của bạn": "Your data stays on this PC", "Thông tin thiết bị": "Device information",
    "Máy tính của bạn": "Your computer", "Xem nhanh cấu hình và tình trạng cơ bản của máy. WinAssist không thay đổi thiết lập khi đọc thông tin này.": "See your PC specifications and basic status. WinAssist does not change any settings while reading this information.",
    "Đọc lại thông số": "Refresh specifications", "Đang đọc thông số máy…": "Reading PC specifications…",
    "Mở trợ lý": "Open assistant", "Chẩn đoán máy": "Diagnose PC", "Kiểm tra mạng": "Check network",
    "Kiểm tra Wi-Fi": "Check Wi-Fi", "Đo tốc độ": "Speed test", "Cài ứng dụng": "Install apps",
    "Xin chào, bạn đang cần kiểm tra máy hay cài thêm ứng dụng?": "Hello, would you like to check your PC or install an app?",
    "Trước khi thay đổi máy, WinAssist luôn cho bạn xem lại và xác nhận.": "WinAssist always shows what will change and asks for confirmation first.",
    "Nhập yêu cầu": "Enter your request", "Gửi": "Send", "Ứng dụng thường dùng": "Popular apps",
    "Chọn ứng dụng phù hợp. Bạn luôn được hỏi lại trước khi cài hoặc gỡ.": "Choose an app. WinAssist always asks before installing or uninstalling.",
    "Đang chuẩn bị": "Getting ready", "Quét lại": "Scan again", "Phổ thông": "Everyday",
    "Trình duyệt, văn phòng, nghe nhạc và game": "Browsers, office, music and games", "Chuyên sâu": "Professional",
    "Lập trình, marketing, văn phòng và quản trị hệ thống": "Development, marketing, office and system tools",
    "Kiểm tra và khắc phục": "Check and troubleshoot", "Việc kiểm tra không làm thay đổi máy. Mọi thao tác sửa chữa đều cần bạn xác nhận.": "Checks do not change your PC. Every repair requires your confirmation.",
    "Kiểm tra mạng đầy đủ": "Full network check", "Adapter, IP, gateway, DNS, Wi-Fi và kết nối Internet.": "Adapter, IP, gateway, DNS, Wi-Fi and internet connection.",
    "Chạy kiểm tra": "Run check", "Đo tốc độ mạng": "Internet speed test", "Download, upload, ping và jitter qua Ookla CLI.": "Download, upload, ping and jitter using Ookla.",
    "Kiểm tra Windows phổ thông": "Common Windows checks", "Pin, ổ đĩa, thiết bị, máy in, ngày giờ và startup.": "Battery, storage, devices, printers, date, time and startup apps.",
    "Quét tất cả": "Scan all", "Sửa chữa nhanh": "Quick fixes", "Kiểm tra và cập nhật phần mềm giúp hình ảnh, video và trò chơi hoạt động ổn định.": "Check software updates that keep images, video and games running smoothly.",
    "Kiểm tra cập nhật": "Check for updates", "Chưa kiểm tra": "Not checked", "Nhấn kiểm tra để xem card màn hình có công cụ cập nhật phù hợp hay không.": "Run the check to find the right graphics update tool.",
    "Tìm bản cập nhật mới, xem lần cập nhật gần nhất và yêu cầu khởi động lại.": "Find new updates, see the latest update and check whether a restart is needed.",
    "Kiểm tra máy": "Check PC", "Nhấn kiểm tra để WinAssist giải thích tình trạng cập nhật bằng nội dung dễ hiểu.": "Run the check for a simple explanation of your update status.",
    "Tìm và cài bản cập nhật": "Find and install updates", "Hiện tại WinAssist mở trang cập nhật an toàn của Windows để bạn xem và cài. App chưa tự cài trực tiếp.": "WinAssist opens the official Windows Update page where you can review and install updates.",
    "Kiểm tra và cập nhật": "Check and update", "Hoạt động gần đây": "Recent activity", "Theo dõi yêu cầu đang chờ, đang chạy và đã hoàn tất.": "View pending, running and completed tasks.",
    "Làm mới": "Refresh", "Tự kiểm tra phiên bản mới và xem những thay đổi trước khi cập nhật.": "Check for a new version and see what changed before updating.",
    "WinAssist sẽ tự kiểm tra khi ứng dụng khởi động.": "WinAssist checks automatically when the app starts.", "Kiểm tra ngay": "Check now",
    "Có gì mới?": "What's new?", "Đang tải thông tin phiên bản…": "Loading version information…",
    "Gặp lỗi hoặc chưa biết cách sử dụng? Hãy gửi thông tin để được hỗ trợ.": "Found a problem or need help? Send us the details.",
    "Báo lỗi qua email": "Report by email", "Phù hợp nếu bạn không dùng GitHub. Hãy mô tả lỗi và đính kèm ảnh chụp màn hình.": "Best if you do not use GitHub. Describe the problem and attach a screenshot.",
    "Gửi email hỗ trợ": "Email support", "Báo lỗi trên GitHub": "Report on GitHub", "Phù hợp nếu bạn có tài khoản GitHub và muốn theo dõi tiến độ xử lý.": "Best if you have a GitHub account and want to track progress.",
    "Tạo báo cáo lỗi": "Create bug report", "Chỉ cần gửi 3 thông tin": "Please include 3 details",
    "Bạn đang làm gì trước khi lỗi xuất hiện.": "What you were doing before the problem appeared.", "Ảnh chụp thông báo lỗi hoặc màn hình bị lỗi.": "A screenshot of the message or problem.",
    "Phiên bản Windows và WinAssist đang dùng.": "Your Windows and WinAssist versions.", "Không gửi mật khẩu, mã xác thực hoặc thông tin tài khoản cá nhân.": "Do not send passwords, verification codes or private account information.",
    "Xóa WinAssist khỏi máy mà không ảnh hưởng đến các tiện ích bạn đã cài.": "Remove WinAssist without affecting apps installed through it.",
    "Chỉ gỡ WinAssist": "Remove WinAssist only", "Các ứng dụng như Chrome, Discord, Steam hoặc VS Code vẫn được giữ nguyên.": "Apps such as Chrome, Discord, Steam and VS Code will remain installed.",
    "Đang kiểm tra bộ gỡ cài đặt…": "Checking the uninstaller…", "Xác nhận": "Confirm", "Xem lại thao tác": "Review action",
    "Thông tin kỹ thuật": "Technical information", "Quay lại": "Go back", "Tiếp tục": "Continue", "Đóng WinAssist": "Close WinAssist",
    "Bạn muốn đóng ứng dụng thế nào?": "How would you like to close the app?", "Chọn một cách đóng bên dưới.": "Choose one option below.",
    "Cách đóng WinAssist": "How to close WinAssist", "Thu nhỏ xuống khay": "Minimize to tray", "WinAssist vẫn chạy và có thể mở lại nhanh.": "WinAssist keeps running and can be reopened quickly.",
    "Thoát hoàn toàn": "Exit completely", "Đóng WinAssist và dừng các tiến trình nền.": "Close WinAssist and stop background processes.",
    "Xác nhận gỡ ứng dụng": "Confirm uninstall", "Gỡ WinAssist khỏi máy?": "Uninstall WinAssist?", "WinAssist sẽ đóng, xóa thư mục cài đặt cùng dữ liệu riêng như lịch sử và log.": "WinAssist will close and remove its app data, including history and logs.",
    "Các tiện ích bạn đã cài sẽ không bị gỡ.": "Apps installed through WinAssist will not be removed.",
    "Bạn cần hỗ trợ gì trên Windows?": "What do you need help with on Windows?",
    "Điểm mới": "What's new", "Đã sửa": "Fixed", "An toàn": "Safety",
    "Bình thường": "All good", "Đang tải…": "Loading…", "Thử lại": "Try again", "Ngôn ngữ": "Language",
    "Cài": "Install", "Gỡ": "Uninstall", "Hủy": "Cancel", "Mở": "Open", "Kiểm tra": "Check",
    "Bạn": "You", "Bạn có thể chọn:": "You can choose:", "Chuẩn bị": "Preparing", "Chỉ đọc": "Read only",
    "Chờ xác nhận": "Waiting for confirmation", "Cài đặt": "Install", "Gỡ cài đặt": "Uninstall",
    "Hoàn tất": "Completed", "Thất bại": "Failed", "Hết hạn": "Expired", "Đang chạy": "Running",
    "Đang hủy": "Cancelling", "Đã hủy": "Cancelled", "Cần chú ý": "Needs attention",
    "Không khả dụng": "Unavailable", "Không kiểm tra được": "Could not check", "Không xác định": "Unknown",
    "Không có": "None", "Có": "Yes", "Không": "No", "Kiểm tra lại": "Check again",
    "Thực hiện": "Continue", "Tải và cập nhật": "Download and update", "Xem dữ liệu kỹ thuật": "View technical details",
    "Bộ xử lý": "Processor", "Bộ nhớ RAM": "Memory (RAM)", "Hệ điều hành": "Operating system",
    "Phiên bản Windows": "Windows version", "Máy tính Windows": "Windows PC", "Đồ họa": "Graphics",
    "Máy in": "Printers", "Thiết bị": "Devices", "Thiết bị hình ảnh": "Imaging devices",
    "Thiết bị media": "Media devices", "Âm thanh / microphone": "Audio / microphone",
    "Ngày giờ hiện tại": "Current date and time", "Múi giờ": "Time zone", "Tự chạy cùng Windows": "Starts with Windows",
    "Trình duyệt": "Browsers", "Văn phòng & PDF": "Office & PDF", "Đa phương tiện": "Media",
    "Game & giải trí": "Games & entertainment", "Công cụ phát triển": "Developer tools",
    "Dành cho lập trình": "Development", "Marketing & sáng tạo": "Marketing & creative",
    "Văn phòng chuyên sâu": "Advanced office", "Quản trị hệ thống": "System administration",
    "Đang đọc…": "Reading…", "Đang quét…": "Scanning…", "Đang kiểm tra…": "Checking…",
    "Đang chạy kiểm tra…": "Running check…", "Đang quét ứng dụng trên máy…": "Scanning apps on this PC…",
    "Đang chuẩn bị các mục kiểm tra…": "Preparing checks…", "Đang kết nối lại theo dõi trực tiếp…": "Reconnecting live updates…",
    "Chưa kiểm tra được": "Could not check", "Chưa đọc được phiên bản hiện tại": "Could not read the current version",
    "Không đọc được thông số máy": "Could not read PC specifications", "Không có trên máy": "Not found on this PC",
    "Ứng dụng không có tên": "Unnamed app", "Danh sách sẽ hiện sau khi kiểm tra xong các ứng dụng.": "The list will appear after the app scan finishes.",
    "Chưa có hoạt động nào.": "No recent activity.", "Hoạt động bình thường": "Working normally",
    "Trạng thái cập nhật": "Update status", "Bản cập nhật mới": "New updates", "Bản cập nhật Windows": "Windows updates",
    "Lần cập nhật gần nhất": "Latest update", "Máy có cần khởi động lại?": "Does the PC need a restart?",
    "Máy đang dùng các bản cập nhật mới nhất mà Windows tìm thấy.": "Your PC has the latest updates found by Windows.",
    "Bạn có thể tiếp tục sử dụng máy bình thường.": "You can continue using your PC normally.",
    "Bạn có thể xem và cài bằng nút bên dưới.": "You can review and install them using the button below.",
    "Hãy lưu công việc trước khi khởi động lại.": "Save your work before restarting.",
    "Đang tìm các bản cập nhật mới… Việc này có thể mất vài phút.": "Looking for new updates… This may take a few minutes.",
    "Đang kiểm tra card màn hình và phiên bản hiện tại…": "Checking graphics hardware and its current version…",
    "Đã nhận diện card màn hình": "Graphics hardware detected", "Mở trang tải chính hãng": "Open official download page",
    "Trợ lý: chế độ cơ bản": "Assistant: basic mode", "Trợ lý: sẵn sàng": "Assistant: ready",
    "Backend không kết nối": "Service is not connected", "Đang chờ xác nhận — chưa tải xuống": "Waiting for confirmation — download has not started",
    "Đã hủy yêu cầu; installer chưa được chạy.": "Request cancelled; the installer was not started.",
    "WinAssist đã có phiên bản ứng dụng Windows": "WinAssist is now a Windows app",
    "Bạn có thể mở WinAssist như một ứng dụng bình thường mà không cần tự khởi động backend hoặc mở trình duyệt.": "You can open WinAssist like a normal app without starting services or a browser yourself.",
    "WinAssist giờ hoạt động như một ứng dụng Windows bình thường.": "WinAssist now works like a regular Windows app.",
    "Có thêm mục kiểm tra card màn hình và cập nhật Windows.": "Added graphics and Windows Update checks.",
    "Kho Tiện ích có thêm nhiều ứng dụng phổ biến cho học tập, làm việc và giải trí.": "Added more popular apps for study, work and entertainment.",
    "WinAssist tự báo khi có phiên bản mới.": "WinAssist notifies you when a new version is available.",
    "Có thể chuyển giao diện giữa tiếng Việt và tiếng Anh.": "You can switch the interface between Vietnamese and English.",
    "Có thể gửi báo cáo lỗi và ảnh chụp ngay trong WinAssist.": "You can send bug reports and screenshots directly from WinAssist.",
    "Mở và đóng ứng dụng ổn định hơn.": "The app opens and closes more reliably.",
    "Trạng thái ứng dụng đã cài được cập nhật chính xác hơn.": "Installed app status is now more accurate.",
    "Giao diện mới được hiển thị đúng sau khi cập nhật.": "The latest interface now appears correctly after an update.",
    "Dữ liệu sử dụng được giữ trên máy của bạn.": "Your usage data stays on your PC.",
    "WinAssist luôn hỏi lại trước khi cài, gỡ hoặc thay đổi máy.": "WinAssist always asks before installing, removing or changing anything.",
    "Theo dõi tiện ích theo thời gian thực": "Live app tracking",
    "WinAssist phản hồi nhanh hơn, tự nhận biết thay đổi ứng dụng từ Windows và có giao diện Fluent nhất quán.": "WinAssist responds faster, detects app changes and has a more consistent interface.",
    "Tự phát hiện ứng dụng được cài hoặc gỡ từ bên ngoài WinAssist.": "Detects apps installed or removed outside WinAssist.",
    "Tab Tiện ích cập nhật nhanh hơn và không quét lại liên tục.": "The Apps tab updates faster without constant rescanning.",
    "Có thêm mục xem nội dung phiên bản mới.": "Added a page showing what's included in each version.",
    "Giao diện giữa các mục đã đồng nhất và dễ nhìn hơn.": "Pages are now more consistent and easier to read.",
    "Không quét lại thông số máy mỗi khi quay lại tab Tổng quan.": "PC specifications are no longer rescanned whenever you return to Overview.",
    "Không quét lại toàn bộ kho tiện ích mỗi khi chuyển tab.": "The app list is no longer fully rescanned whenever you change pages.",
    "Kết quả chẩn đoán hiển thị ngay trong đúng thẻ tương ứng.": "Diagnostic results now appear in the relevant card.",
    "Nút cài, gỡ và hủy lớn hơn, rõ trạng thái và cập nhật trực tiếp.": "Install, uninstall and cancel buttons are clearer and update live.",
    "WinAssist chỉ đọc danh sách ứng dụng và không tự sửa thiết lập Windows.": "WinAssist only reads the app list and does not change Windows settings automatically.",
    "Bạn luôn được hỏi lại trước khi cài hoặc gỡ ứng dụng.": "You are always asked before an app is installed or removed.",
    "WinAssist khởi động ổn định hơn": "More reliable WinAssist startup",
    "Sửa lỗi một số máy không mở được WinAssist sau khi hoàn tất Setup.": "Fixed an issue that prevented WinAssist from opening after Setup on some PCs.",
    "Có thể chuyển giao diện và phản hồi trợ lý giữa tiếng Việt và tiếng Anh.": "You can switch the interface and assistant responses between Vietnamese and English.",
    "Có thể gửi báo cáo lỗi kèm ảnh ngay trong WinAssist.": "You can send bug reports with screenshots directly from WinAssist.",
    "Sửa lỗi WinAssist không mở được sau khi cài đặt.": "Fixed an issue that prevented WinAssist from opening after installation.",
    "Sửa thông báo thất bại giả sau khi ticket đã gửi thành công.": "Fixed a false failure message after a ticket was sent successfully.",
    "Ghi lại chi tiết lỗi khởi động để hỗ trợ dễ hơn.": "Startup error details are now saved for easier support.",
    "Ticket chỉ được gửi đến dịch vụ hỗ trợ chính thức của WinAssist.": "Tickets are sent only to the official WinAssist support service.",
    "Mọi thao tác thay đổi máy vẫn cần bạn xác nhận.": "Any action that changes your PC still requires confirmation.",
    "Hotfix giao diện": "Interface hotfix",
    "Thanh cuộn và khoảng cách nội dung đã gọn gàng, dễ nhìn hơn.": "Scrollbars and content spacing are now cleaner and easier to view.",
    "Thanh cuộn nằm đúng sát mép cửa sổ.": "The scrollbar now sits correctly at the edge of the window.",
    "Nội dung có khoảng cách đều trên mọi mục.": "Content spacing is consistent across all pages.",
    "Sửa khoảng trống bất thường cạnh thanh cuộn.": "Fixed the unexpected gap beside the scrollbar.",
    "Giữ bố cục ổn định trên màn hình nhỏ.": "Kept the layout stable on smaller screens.",
    "Hotfix chỉ thay đổi giao diện, không thay đổi dữ liệu hoặc quyền hệ thống.": "This hotfix only changes the interface and does not affect data or system permissions.",
    "Cập nhật ngay trong WinAssist": "Update directly in WinAssist",
    "Từ phiên bản này, các bản mới có thể được tải và cài ngay trong ứng dụng.": "Starting with this version, new releases can be downloaded and installed directly in the app.",
    "Xem tiến trình tải bản cập nhật theo thời gian thực.": "See update download progress in real time.",
    "Có thể hủy khi bản cập nhật đang tải.": "Cancel while an update is downloading.",
    "WinAssist tự đóng và mở lại sau khi cập nhật.": "WinAssist closes and reopens automatically after updating.",
    "Không còn phải tự mở file Setup cho các lần cập nhật tiếp theo.": "You no longer need to open Setup manually for future updates.",
    "Chỉ nhận installer từ GitHub chính thức và kiểm tra SHA-256 trước khi cài.": "Only installers from the official GitHub release are accepted and SHA-256 is verified before installation.",
    "Gỡ WinAssist sạch hơn": "Cleaner WinAssist uninstall",
    "Gỡ WinAssist sạch hơn mà không ảnh hưởng đến các tiện ích khác.": "Remove WinAssist cleanly without affecting other installed apps.",
    "WinAssist chờ ứng dụng đóng hẳn rồi mới xóa các file cài đặt.": "WinAssist now waits until the app fully closes before removing installation files.",
    "Sửa lỗi WinAssist.exe và thư mục _internal còn sót sau khi gỡ ứng dụng.": "Fixed WinAssist.exe and the _internal folder remaining after uninstall.",
    "Chỉ xóa thư mục của WinAssist; các tiện ích đã cài không bị ảnh hưởng.": "Only WinAssist folders are removed; installed apps are not affected.",
    "Bạn đang gặp lỗi gì?": "What problem are you having?", "Chọn một mục": "Choose an option",
    "Không mở được WinAssist": "WinAssist does not open", "Không cài được tiện ích": "An app will not install",
    "Không gỡ được ứng dụng": "An app will not uninstall", "Kiểm tra máy hoặc mạng bị lỗi": "PC or network check failed",
    "Lỗi cập nhật": "Update problem", "Trợ lý trả lời chưa đúng": "Assistant response is incorrect",
    "Giao diện hoặc nút bấm bị lỗi": "Interface or button problem", "Lỗi khác": "Other problem",
    "Mô tả lỗi": "Describe the problem", "Bạn đã làm gì và lỗi xuất hiện như thế nào?": "What were you doing and how did the problem appear?",
    "Ảnh chụp màn hình": "Screenshot", "(không bắt buộc, PNG/JPG/WebP, tối đa 5 MB)": "(optional, PNG/JPG/WebP, up to 5 MB)",
    "Gửi báo cáo": "Send report", "Đang gửi…": "Sending…", "Hãy lưu mã này để đối chiếu khi cần hỗ trợ tiếp.": "Keep this number for future support."
  };

  const sourceText = new WeakMap();
  const renderedText = new WeakMap();
  const sourceAttributes = new WeakMap();
  let language = localStorage.getItem(STORAGE_KEY) === "en" ? "en" : "vi";

  function translated(value) {
    if (language !== "en") return value;
    if (en[value]) return en[value];
    const prefixes = [
      ["Phiên bản ", "Version "], ["Phát hành ngày ", "Released on "],
      ["Đã cài · ", "Installed · "], ["Cài ngày ", "Installed on "],
      ["Đã gửi ", "Sent "],
      ["Không thể tải thông tin phiên bản: ", "Could not load version information: "],
    ];
    const match = prefixes.find(([source]) => value.startsWith(source));
    return match ? `${match[1]}${value.slice(match[0].length)}` : value;
  }
  function translateTextNode(node) {
    const current = node.nodeValue;
    if (!current || !current.trim()) return;
    if (!sourceText.has(node) || current !== renderedText.get(node)) sourceText.set(node, current);
    const source = sourceText.get(node);
    const clean = source.trim();
    const next = source.replace(clean, translated(clean));
    renderedText.set(node, next);
    if (current !== next) node.nodeValue = next;
  }
  function translateElement(node) {
    if (!(node instanceof Element)) return;
    const originals = sourceAttributes.get(node) || {};
    ["placeholder", "aria-label", "title"].forEach((name) => {
      if (!node.hasAttribute(name)) return;
      if (!(name in originals)) originals[name] = node.getAttribute(name);
      node.setAttribute(name, translated(originals[name]));
    });
    sourceAttributes.set(node, originals);
  }
  function translateTree(root = document.body) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) translateTextNode(root);
    if (root.nodeType === Node.ELEMENT_NODE) translateElement(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      if (walker.currentNode.nodeType === Node.TEXT_NODE) translateTextNode(walker.currentNode);
      else translateElement(walker.currentNode);
    }
    document.documentElement.lang = language;
    document.querySelectorAll("[data-language]").forEach((button) => {
      const active = button.dataset.language === language;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }
  function setLanguage(next) {
    if (next !== "vi" && next !== "en") return;
    language = next;
    localStorage.setItem(STORAGE_KEY, language);
    translateTree();
    window.dispatchEvent(new CustomEvent("winassist:languagechange", { detail: { language } }));
  }

  window.WinAssistI18n = { get language() { return language; }, setLanguage, t: translated, refresh: translateTree };
  document.querySelectorAll("[data-language]").forEach((button) => button.addEventListener("click", () => setLanguage(button.dataset.language)));
  new MutationObserver((records) => records.forEach((record) => {
    if (record.type === "characterData") translateTextNode(record.target);
    record.addedNodes.forEach(translateTree);
  })).observe(document.body, { subtree: true, childList: true, characterData: true });
  translateTree();
})();
