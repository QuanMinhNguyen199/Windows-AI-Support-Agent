from pathlib import Path

from app.parsers.netsh_wlan_parser import parse_wlan_interfaces


def test_parse_wifi_information() -> None:
    fixture = Path(__file__).parent / "fixtures" / "wifi_connected.txt"
    wifi = parse_wlan_interfaces(
        fixture.read_text(encoding="utf-8"),
        "    Driver                 : Intel Wi-Fi Driver\n",
    )

    assert wifi.state == "connected"
    assert wifi.ssid == "HomeNetwork"
    assert wifi.signal_percent == 72
    assert wifi.receive_rate_mbps == 866.7
    assert wifi.driver == "Intel Wi-Fi Driver"
