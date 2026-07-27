from pathlib import Path

from app.parsers.ping_parser import describe_ping, parse_ping


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_successful_ping() -> None:
    statistics = parse_ping(
        (FIXTURES / "ping_success.txt").read_text(encoding="utf-8")
    )

    assert statistics.sent == 4
    assert statistics.received == 4
    assert statistics.loss_percent == 0
    assert statistics.minimum_ms == 15
    assert statistics.maximum_ms == 18
    assert statistics.average_ms == 16
    assert describe_ping(statistics)[0] == "success"


def test_parse_ping_with_packet_loss() -> None:
    statistics = parse_ping((FIXTURES / "ping_loss.txt").read_text(encoding="utf-8"))

    assert statistics.lost == 2
    assert statistics.loss_percent == 50
    assert describe_ping(statistics)[0] == "error"


def test_parse_vietnamese_ping_output() -> None:
    statistics = parse_ping(
        (FIXTURES / "ping_success_vi.txt").read_text(encoding="utf-8")
    )

    assert statistics.sent == 2
    assert statistics.received == 2
    assert statistics.loss_percent == 0
    assert statistics.average_ms == 19
