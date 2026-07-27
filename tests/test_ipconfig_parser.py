from pathlib import Path

from app.parsers.ipconfig_parser import parse_ipconfig


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_normal_ip_configuration() -> None:
    configuration = parse_ipconfig(
        (FIXTURES / "ipconfig_normal.txt").read_text(encoding="utf-8")
    )

    assert configuration.ipv4_addresses == ["192.168.1.25"]
    assert configuration.default_gateway == "192.168.1.1"
    assert configuration.dns_servers == ["192.168.1.1", "1.1.1.1"]
    assert configuration.has_apipa is False
    assert configuration.connected_adapters == ["Wireless LAN adapter Wi-Fi"]


def test_detect_apipa_address() -> None:
    configuration = parse_ipconfig(
        (FIXTURES / "ipconfig_apipa.txt").read_text(encoding="utf-8")
    )

    assert configuration.has_apipa is True
    assert configuration.default_gateway is None
