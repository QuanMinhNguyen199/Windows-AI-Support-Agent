import re

from app.models.chat import ChatResponse


ENGLISH_TEXT = {
    "Xin chào! Tôi có thể kiểm tra phần mềm, chẩn đoán mạng và chuẩn bị hành động cài đặt an toàn.": "Hello! I can check software, diagnose network issues, and prepare safe installation actions.",
    "Bạn muốn kiểm tra máy, kết nối mạng hay cài ứng dụng?": "Would you like to check your PC, troubleshoot the network, or install an app?",
    "Máy chạy chậm": "Slow PC", "Mạng có vấn đề": "Network problem", "Cài ứng dụng": "Install apps",
    "Kiểm tra Windows": "Check Windows", "Khởi động máy chậm": "Slow startup", "Ổ đĩa gần đầy": "Storage almost full",
    "Internet chậm": "Slow internet", "Quét tình trạng máy": "Scan PC status", "Không vào được mạng": "No internet access",
    "Kiểm tra ứng dụng": "Check apps", "Máy của tôi đang chạy chậm": "My PC is running slowly",
    "Kiểm tra kết nối mạng của tôi": "Check my network connection", "Kiểm tra ứng dụng khởi động cùng Windows": "Check apps that start with Windows",
    "Kiểm tra dung lượng ổ đĩa": "Check storage space", "Mạng của tôi đang chậm": "My internet is slow",
    "Máy của tôi không vào được mạng": "My PC cannot access the internet",
    "Máy chậm có thể do ứng dụng khởi động, ổ đĩa gần đầy, cấu hình hoặc kết nối mạng. Vấn đề của bạn gần với trường hợp nào?": "A slow PC can be caused by startup apps, low storage, hardware, or the network. Which case is closest to your problem?",
    "Catalog hiện có các ứng dụng phổ thông và công cụ phát triển sau.": "The catalog contains the following everyday and developer apps.",
    "Hãy chọn theo nhu cầu; ứng dụng chỉ được cài sau khi bạn xác nhận.": "Choose what you need; an app is installed only after you confirm.",
    "Gateway, kết nối IP Internet và phân giải DNS đều phản hồi.": "The gateway, internet IP connection, and DNS resolution are responding.",
    "Nếu ứng dụng vẫn lỗi, kiểm tra proxy, VPN, trình duyệt hoặc firewall của ứng dụng.": "If an app still has problems, check its proxy, VPN, browser, or firewall settings.",
    "Chưa phát hiện lỗi kết nối mạng cơ bản.": "No basic network connection problem was detected.",
    "Kiểm tra Wi-Fi đã bật hoặc cáp Ethernet đã kết nối.": "Check that Wi-Fi is on or the Ethernet cable is connected.",
    "Kiểm tra Wi-Fi/Ethernet đã kết nối và DHCP trên router.": "Check the Wi-Fi/Ethernet connection and DHCP on the router.",
    "Kiểm tra router/DHCP và thử kết nối lại Wi-Fi hoặc cáp mạng.": "Check the router and DHCP, then reconnect Wi-Fi or Ethernet.",
    "Kiểm tra cấu hình IP/DHCP của adapter đang hoạt động.": "Check the IP and DHCP settings of the active adapter.",
    "Kiểm tra tín hiệu Wi-Fi, cáp mạng và trạng thái router.": "Check Wi-Fi signal, the network cable, and router status.",
    "Kiểm tra DNS đang cấu hình; có thể cân nhắc flush DNS sau khi xác nhận.": "Check the configured DNS; you may flush DNS after confirming the action.",
    "Kiểm tra trạng thái WAN của router hoặc liên hệ ISP.": "Check the router WAN status or contact your internet provider.",
    "Di chuyển gần router hoặc giảm vật cản/nhiễu Wi-Fi.": "Move closer to the router or reduce Wi-Fi obstacles and interference.",
    "Tín hiệu Wi-Fi ở mức trung bình; theo dõi packet loss khi sử dụng.": "Wi-Fi signal is moderate; watch for packet loss while using it.",
    "Chạy lại kiểm tra và xem lỗi chi tiết của từng command.": "Run the check again and review the details of each failed step.",
    "Packet loss và ping chỉ là ngưỡng tham khảo; nên kiểm tra nhiều thời điểm.": "Packet loss and ping are only reference values; test at different times.",
    "Đã hoàn tất phép đo tốc độ mạng.": "The internet speed test is complete.",
    "Kết quả có thể thay đổi theo thời điểm và máy chủ đo.": "Results may vary by time and test server.",
    "Speed test chưa được cấu hình.": "Speed test is not configured.",
    "Cài Ookla Speedtest CLI trong Suggestions rồi thử lại.": "Install Ookla Speedtest CLI from Apps and try again.",
    "Tôi chưa xác định được phần nào đang gặp vấn đề. Bạn có thể chọn một hướng kiểm tra bên dưới.": "I could not identify the problem yet. Choose a check below.",
    "Bạn muốn kiểm tra hoặc cài phần mềm nào trong catalog?": "Which catalog app would you like to check or install?",
    "Kiểm tra command preview trước khi bấm Xác nhận.": "Review the action details before selecting Confirm.",
    "Phần mềm được nhắc đến không nằm trong catalog đã kiểm duyệt.": "The requested app is not in the reviewed catalog.",
    "Yêu cầu chứa chỉ dẫn có thể làm suy yếu quy tắc an toàn nên không được gửi tới AI.": "The request contains instructions that may weaken safety rules, so it was not sent to AI.",
    "Tôi đang dùng hướng dẫn an toàn có sẵn trên máy.": "I am using the safe guidance available on this PC.",
    "Trợ lý thông minh chưa phản hồi; tôi đang dùng hướng dẫn có sẵn trên máy.": "The local AI did not respond, so I am using the guidance available on this PC.",
    "Không thể dùng AI để tóm tắt; đang hiển thị kết luận deterministic.": "AI could not summarize the result, so the verified conclusion is shown instead.",
}


def translate_text(text: str | None, language: str) -> str | None:
    if text is None or language != "en":
        return text
    if text in ENGLISH_TEXT:
        return ENGLISH_TEXT[text]
    patterns = (
        (r"^Đã kiểm tra (\d+) nhóm hỗ trợ Windows\.$", r"Checked \1 Windows support areas."),
        (r"^Đã phát hiện (\d+) ổ đĩa cục bộ\.$", r"Found \1 local drives."),
        (r"^Đã phát hiện (\d+) thiết bị liên quan\.$", r"Found \1 related devices."),
        (r"^Có (\d+) bản cập nhật mới đang chờ bạn xem và cài\.$", r"There are \1 new updates ready for review and installation."),
    )
    for pattern, replacement in patterns:
        if re.match(pattern, text):
            return re.sub(pattern, replacement, text)
    return text


def localize_response(response: ChatResponse, language: str) -> ChatResponse:
    if language != "en":
        return response
    return response.model_copy(
        update={
            "message": translate_text(response.message, language),
            "warning": translate_text(response.warning, language),
            "recommendations": [translate_text(item, language) for item in response.recommendations],
            "suggestions": [
                item.model_copy(update={"label": translate_text(item.label, language), "message": translate_text(item.message, language)})
                for item in response.suggestions
            ],
        }
    )
