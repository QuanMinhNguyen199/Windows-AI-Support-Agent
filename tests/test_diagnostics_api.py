from pathlib import Path

from fastapi.testclient import TestClient

from app.api.diagnostics import get_network_service
from app.main import app
from app.models.command import CommandDefinition, CommandResult
from app.services.network_service import NetworkService


FIXTURES = Path(__file__).parent / "fixtures"


class APIFakeRunner:
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult:
        outputs = {
            "network.get_adapters": '[{"Name":"Wi-Fi","Status":"Up"}]',
            "network.ipconfig_all": (FIXTURES / "ipconfig_normal.txt").read_text(
                encoding="utf-8"
            ),
            "network.wifi_interfaces": (FIXTURES / "wifi_connected.txt").read_text(
                encoding="utf-8"
            ),
            "network.wifi_drivers": "Driver : Intel Wi-Fi Driver",
            "network.ping_localhost": (FIXTURES / "ping_success.txt").read_text(
                encoding="utf-8"
            ),
            "network.ping_gateway": (FIXTURES / "ping_success.txt").read_text(
                encoding="utf-8"
            ),
            "network.ping_public_dns": (FIXTURES / "ping_success.txt").read_text(
                encoding="utf-8"
            ),
            "network.ping_google": (FIXTURES / "ping_success.txt").read_text(
                encoding="utf-8"
            ),
            "network.nslookup_google": "Name: google.com\nAddress: 142.250.1.1",
        }
        output = outputs.get(definition.id, "[]")
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=0,
            stdout=output,
            stderr="",
            duration_ms=1,
            timed_out=False,
            success=True,
        )


def test_ping_api_uses_whitelisted_target() -> None:
    app.dependency_overrides[get_network_service] = lambda: NetworkService(
        runner=APIFakeRunner()
    )
    try:
        with TestClient(app) as client:
            response = client.post("/api/diagnostics/ping", json={"target": "1.1.1.1"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["resolved_target"] == "1.1.1.1"
    assert response.json()["statistics"]["loss_percent"] == 0


def test_ping_api_rejects_arbitrary_target() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/diagnostics/ping",
            json={"target": "example.com & whoami"},
        )

    assert response.status_code == 422


def test_network_diagnostic_api_uses_injected_runner() -> None:
    app.dependency_overrides[get_network_service] = lambda: NetworkService(
        runner=APIFakeRunner()
    )
    try:
        with TestClient(app) as client:
            response = client.post("/api/diagnostics/network")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["ip_configuration"]["default_gateways"] == ["192.168.1.1"]
