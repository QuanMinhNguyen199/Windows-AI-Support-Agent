from __future__ import annotations

from app.models.command import CommandResult


def explain_command_failure(result: CommandResult | None) -> tuple[str | None, list[str]]:
    """Turn a redacted command failure into short, non-technical guidance."""
    if result is None or result.success:
        return None, []
    output = f"{result.stdout}\n{result.stderr}".casefold()
    if result.timed_out:
        return (
            "Trình cài đặt mất nhiều thời gian hơn dự kiến.",
            ["Kiểm tra mạng, đóng cửa sổ cài đặt còn mở rồi thử lại."],
        )
    if result.exit_code is None and "executable was not found" in output:
        return (
            "Máy chưa có Windows Package Manager (winget).",
            ["Cập nhật App Installer từ Microsoft Store rồi thử lại."],
        )
    if any(value in output for value in ("0x800704c7", "cancelled", "canceled")):
        return (
            "Quá trình cài đặt đã bị hủy.",
            ["Thử lại và hoàn tất cửa sổ xác nhận của Windows nếu xuất hiện."],
        )
    if any(value in output for value in ("0x80070005", "access is denied", "permission denied", "elevation")):
        return (
            "Windows chưa cho phép cài ứng dụng này.",
            ["Thử lại và chấp nhận yêu cầu quyền quản trị nếu Windows hỏi."],
        )
    if any(value in output for value in ("0x8a15000f", "source data", "failed when searching source", "source named")):
        return (
            "Nguồn ứng dụng của winget chưa sẵn sàng.",
            ["Kiểm tra mạng, mở Microsoft Store một lần rồi thử lại."],
        )
    if any(value in output for value in ("0x80072", "network", "internet", "download failed", "connection")):
        return (
            "Không tải được bộ cài từ Internet.",
            ["Kiểm tra Wi-Fi, VPN, proxy hoặc tường lửa rồi thử lại."],
        )
    if any(value in output for value in ("no package found", "no applicable installer", "package not found")):
        return (
            "Ứng dụng này hiện chưa có bộ cài phù hợp cho máy.",
            ["Quét lại danh sách hoặc báo lỗi để WinAssist kiểm tra package."],
        )
    if "another installation" in output or result.exit_code == 1618:
        return (
            "Một trình cài đặt khác đang chạy trên Windows.",
            ["Đợi quá trình kia hoàn tất rồi thử lại."],
        )
    return (
        "Trình cài đặt không hoàn tất.",
        ["Thử lại một lần; nếu vẫn lỗi, gửi báo cáo để kèm mã lỗi an toàn."],
    )
