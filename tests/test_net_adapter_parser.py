from app.parsers.net_adapter_parser import parse_net_adapters


def test_parse_adapter_json() -> None:
    output = (
        '[{"Name":"Wi-Fi","InterfaceDescription":"Intel Wireless",'
        '"Status":"Up","LinkSpeed":"866 Mbps"},'
        '{"Name":"Ethernet","Status":"Disconnected","LinkSpeed":"0 bps"}]'
    )

    adapters = parse_net_adapters(output)

    assert len(adapters) == 2
    assert adapters[0].name == "Wi-Fi"
    assert adapters[0].is_up is True
    assert adapters[1].is_up is False


def test_invalid_adapter_output_returns_empty_list() -> None:
    assert parse_net_adapters("not-json") == []
