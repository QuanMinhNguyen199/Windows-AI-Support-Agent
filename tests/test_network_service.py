import asyncio
from pathlib import Path

from app.models.command import CommandDefinition, CommandResult
from app.models.diagnostics import DiagnosticStatus
from app.services.network_service import NetworkService


FIXTURES = Path(__file__).parent / "fixtures"


def result(
    definition: CommandDefinition,
    *,
    stdout: str = "",
    success: bool = True,
) -> CommandResult:
    return CommandResult(
        command_id=definition.id,
        executable=definition.executable,
        arguments=list(definition.arguments),
        exit_code=0 if success else 1,
        stdout=stdout,
        stderr="",
        duration_ms=1,
        timed_out=False,
        success=success,
    )


class FakeRunner:
    def __init__(self, *, dns_success: bool = True, public_ping_success: bool = True):
        self.dns_success = dns_success
        self.public_ping_success = public_ping_success
        self.command_ids: list[str] = []

    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult:
        self.command_ids.append(definition.id)
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
        success = True
        if definition.id == "network.nslookup_google" and not self.dns_success:
            outputs[definition.id] = "DNS request timed out."
            success = False
        if definition.id == "network.ping_public_dns" and not self.public_ping_success:
            outputs[definition.id] = ""
            success = False
        return result(definition, stdout=outputs.get(definition.id, "[]"), success=success)


def test_network_diagnostic_success() -> None:
    runner = FakeRunner()
    response = asyncio.run(NetworkService(runner=runner).run_diagnostic())

    assert response.status is DiagnosticStatus.SUCCESS
    assert response.confidence == "high"
    assert "network.ping_gateway" in runner.command_ids


def test_network_diagnostic_detects_dns_failure() -> None:
    response = asyncio.run(
        NetworkService(runner=FakeRunner(dns_success=False)).run_diagnostic()
    )

    assert response.status is DiagnosticStatus.ERROR
    assert "DNS" in response.likely_cause
    assert response.confidence == "high"
