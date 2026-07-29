import asyncio
import json

from app.core.command_registry import CommandRegistry
from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.models.actions import ActionKind, ActionState
from app.models.command import CommandResult
from app.services.repair_service import RepairService
from app.services.speedtest_service import OoklaSpeedTestProvider


class FakeRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.calls = []

    async def run(self, definition, *, confirmed=False):
        self.calls.append((definition, confirmed))
        return self.result.model_copy(update={
            "command_id": definition.id,
            "executable": definition.executable,
            "arguments": list(definition.arguments),
        })


def result(*, success=True, stdout="") -> CommandResult:
    return CommandResult(
        command_id="placeholder",
        executable="speedtest",
        arguments=[],
        exit_code=0 if success else 1,
        stdout=stdout,
        stderr="",
        duration_ms=10,
        timed_out=False,
        success=success,
    )


def repository(tmp_path) -> PendingActionRepository:
    database = Database(tmp_path / "phase6.db")
    database.initialize()
    return PendingActionRepository(database)


def test_repair_creates_low_risk_pending_action_and_deduplicates(tmp_path) -> None:
    repo = repository(tmp_path)
    service = RepairService(repo, CommandRegistry())

    first = service.request("flush-dns")
    second = service.request("flush-dns")

    assert first.pending_action.id == second.pending_action.id
    assert first.pending_action.kind is ActionKind.NETWORK_REPAIR
    assert first.pending_action.command_id == "repair.flush_dns"
    assert first.pending_action.state is ActionState.PENDING
    assert first.pending_action.display_command == "ipconfig /flushdns"


def test_all_repairs_are_fixed_registry_commands(tmp_path) -> None:
    repo = repository(tmp_path)
    registry = CommandRegistry()
    service = RepairService(repo, registry)

    actions = [service.request(item.id).pending_action for item in service.list_repairs()]

    assert {item.command_id for item in actions} == {
        "repair.flush_dns",
        "repair.release_ip",
        "repair.renew_ip",
    }
    for item in actions:
        registry.assert_registered(repo.get(item.id).definition)


def test_speedtest_parses_ookla_json() -> None:
    payload = {
        "ping": {"jitter": 1.2, "latency": 12.3},
        "download": {"bandwidth": 12_500_000},
        "upload": {"bandwidth": 6_250_000},
        "packetLoss": 0.5,
        "server": {"name": "Example ISP", "location": "Ho Chi Minh City"},
    }
    runner = FakeRunner(result(stdout=json.dumps(payload)))
    provider = OoklaSpeedTestProvider(runner=runner, registry=CommandRegistry())

    response = asyncio.run(provider.run_test())

    assert response.available is True
    assert response.measurement is not None
    assert response.measurement.download_mbps == 100
    assert response.measurement.upload_mbps == 50
    assert response.measurement.ping_ms == 12.3
    assert runner.calls[0][0].id == "network.speedtest"
    assert runner.calls[0][1] is False


def test_speedtest_unavailable_suggests_catalog_entry() -> None:
    provider = OoklaSpeedTestProvider(
        runner=FakeRunner(result(success=False)),
        registry=CommandRegistry(),
    )

    response = asyncio.run(provider.run_test())

    assert response.available is False
    assert response.install_software_id == "speedtest"
