import re

from app.models.diagnostics import PingStatistics


_PACKETS = re.compile(
    r"(?i)"
    r"(?:sent|đ[aã] gửi|gửi)\s*=\s*(?P<sent>\d+).*?"
    r"(?:received|đ[aã] nhận|nhận)\s*=\s*(?P<received>\d+).*?"
    r"(?:lost|bị mất|mất)\s*=\s*(?P<lost>\d+).*?"
    r"\([^0-9]*(?P<loss>\d+(?:[.,]\d+)?)\s*%"
)
_LATENCY = re.compile(
    r"(?i)"
    r"(?:minimum|minimum time|nhỏ nhất|tối thiểu)\s*=\s*(?P<minimum>\d+(?:[.,]\d+)?)\s*ms.*?"
    r"(?:maximum|maximum time|lớn nhất|tối đa)\s*=\s*(?P<maximum>\d+(?:[.,]\d+)?)\s*ms.*?"
    r"(?:average|average time|trung bình)\s*=\s*(?P<average>\d+(?:[.,]\d+)?)\s*ms"
)


def _number(value: str) -> float:
    return float(value.replace(",", "."))


def parse_ping(output: str) -> PingStatistics:
    packet_match = _PACKETS.search(output)
    latency_match = _LATENCY.search(output)
    return PingStatistics(
        sent=int(packet_match.group("sent")) if packet_match else None,
        received=int(packet_match.group("received")) if packet_match else None,
        lost=int(packet_match.group("lost")) if packet_match else None,
        loss_percent=_number(packet_match.group("loss")) if packet_match else None,
        minimum_ms=_number(latency_match.group("minimum")) if latency_match else None,
        maximum_ms=_number(latency_match.group("maximum")) if latency_match else None,
        average_ms=_number(latency_match.group("average")) if latency_match else None,
    )


def describe_ping(statistics: PingStatistics) -> tuple[str, str]:
    if statistics.loss_percent is None:
        return "unknown", "Không đọc được thống kê ping từ output."
    if statistics.loss_percent > 5:
        return "error", f"Packet loss {statistics.loss_percent:g}% là nghiêm trọng."
    if statistics.loss_percent > 2:
        return "error", f"Packet loss {statistics.loss_percent:g}% cho thấy kết nối có vấn đề."
    if statistics.loss_percent > 0:
        return "warning", f"Packet loss {statistics.loss_percent:g}% có thể gây giật nhẹ."
    if statistics.average_ms is None:
        return "success", "Không mất gói; chưa đọc được độ trễ trung bình."
    latency = statistics.average_ms
    if latency < 30:
        label = "rất tốt"
    elif latency < 60:
        label = "tốt"
    elif latency < 100:
        label = "chấp nhận được"
    elif latency < 150:
        label = "cao"
    else:
        label = "rất cao"
    return "success" if latency < 100 else "warning", (
        f"Không mất gói; ping trung bình {latency:g} ms ({label}). "
        "Các ngưỡng chỉ mang tính tham khảo."
    )
