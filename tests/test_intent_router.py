import pytest

from app.core.intent_router import RuleBasedIntentRouter
from app.core.text_normalization import normalize_vietnamese
from app.models.chat import Intent, RouterSource


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Xin chào", Intent.GREETING),
        ("Toi muon cai Firefox", Intent.SOFTWARE_INSTALLATION),
        ("Kiểm tra Python đã cài chưa", Intent.SOFTWARE_CHECK),
        ("Python cài rồi nhưng không chạy", Intent.INSTALLATION_TROUBLESHOOTING),
        ("Máy có Wi-Fi nhưng không vào mạng", Intent.INTERNET_CONNECTION_ISSUE),
        ("Máy của tôi không vào được mạng", Intent.INTERNET_CONNECTION_ISSUE),
        ("Kiểm tra kết nối mạng của tôi", Intent.NETWORK_STATUS),
        ("Check my network connection", Intent.NETWORK_STATUS),
        ("Kiểm tra trạng thái Wi-Fi", Intent.WIFI_DIAGNOSIS),
        ("DNS của tôi có bị lỗi không", Intent.DNS_DIAGNOSIS),
        ("Kiểm tra ping và packet loss", Intent.PACKET_LOSS_DIAGNOSIS),
        ("Kiểm tra tốc độ mạng", Intent.NETWORK_SPEED_TEST),
        ("Máy của tôi đang chạy chậm, tôi nên làm gì", Intent.PERFORMANCE_ISSUE),
        ("Bạn làm được gì?", Intent.HELP),
    ],
)
def test_rule_router_classifies_common_requests(message: str, expected: Intent) -> None:
    decision = RuleBasedIntentRouter().route(message)

    assert decision.intent is expected
    assert decision.source is RouterSource.RULE_BASED


def test_normalize_vietnamese_and_wifi() -> None:
    assert normalize_vietnamese("Kiểm tra Wi-Fi ĐÃ CÀI") == "kiem tra wifi da cai"


def test_router_extracts_only_catalog_software() -> None:
    router = RuleBasedIntentRouter()

    assert router.extract_software_id("Cài VS Code") == "vscode"
    assert router.extract_software_id("Cài unknown-package") is None
