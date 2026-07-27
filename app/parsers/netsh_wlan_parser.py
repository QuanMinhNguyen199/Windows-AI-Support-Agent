import re

from app.models.diagnostics import WifiInformation


_FIELD = re.compile(r"^\s*([^:]+?)\s*:\s*(.*?)\s*$")


def _float(value: str) -> float | None:
    match = re.search(r"\d+(?:[.,]\d+)?", value)
    return float(match.group().replace(",", ".")) if match else None


def _integer(value: str) -> int | None:
    number = _float(value)
    return int(number) if number is not None else None


def parse_wlan_interfaces(output: str, driver_output: str = "") -> WifiInformation:
    values: dict[str, str] = {}
    for line in output.splitlines():
        match = _FIELD.match(line)
        if match:
            values[match.group(1).strip().casefold()] = match.group(2).strip()

    def first(*keys: str) -> str | None:
        for key in keys:
            if key in values:
                return values[key]
        return None

    signal = first("signal", "tín hiệu")
    receive = first("receive rate (mbps)", "tốc độ nhận (mbps)")
    transmit = first("transmit rate (mbps)", "tốc độ truyền (mbps)")
    driver_match = re.search(
        r"(?im)^\s*(?:driver|trình điều khiển)\s*:\s*(.+?)\s*$", driver_output
    )
    return WifiInformation(
        state=first("state", "trạng thái"),
        ssid=first("ssid"),
        signal_percent=_integer(signal) if signal else None,
        radio_type=first("radio type", "loại vô tuyến"),
        receive_rate_mbps=_float(receive) if receive else None,
        transmit_rate_mbps=_float(transmit) if transmit else None,
        channel=_integer(first("channel", "kênh") or ""),
        authentication=first("authentication", "xác thực"),
        driver=driver_match.group(1).strip() if driver_match else None,
    )
