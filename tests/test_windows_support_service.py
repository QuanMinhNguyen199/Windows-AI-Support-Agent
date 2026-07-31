import asyncio
import json

from app.core.command_registry import CommandRegistry
from app.models.command import CommandResult
from app.services.windows_support_service import WindowsSupportService


class FakeRunner:
    def __init__(self, payloads):
        self.payloads = payloads

    async def run(self, definition, *, confirmed=False):
        payload = self.payloads[definition.id]
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=0,
            stdout=json.dumps(payload),
            stderr="",
            duration_ms=1,
            timed_out=False,
            success=True,
        )


def test_storage_warns_when_drive_has_less_than_ten_percent_free() -> None:
    service = WindowsSupportService(
        runner=FakeRunner(
            {
                "windows.storage": {
                    "supported": True,
                    "drives": [
                        {"DeviceID": "C:", "Size": 1000, "FreeSpace": 50}
                    ],
                }
            }
        ),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.inspect("storage"))

    assert response.state == "warning"
    assert "dưới 10%" in response.summary


def test_desktop_without_battery_returns_unavailable() -> None:
    service = WindowsSupportService(
        runner=FakeRunner(
            {"windows.battery": {"supported": False, "batteries": []}}
        ),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.inspect("battery"))

    assert response.state == "unavailable"
    assert response.data["batteries"] == []


def test_privacy_sensitive_fields_are_not_selected_by_commands() -> None:
    registry = CommandRegistry()
    startup = registry.get("windows.startup_apps").display_command.casefold()
    printers = registry.get("windows.printers").display_command.casefold()
    devices = registry.get("windows.devices").display_command.casefold()

    assert "select-object name,location" in startup
    assert " command" not in startup
    assert " user" not in startup
    assert "documentname" not in printers
    assert "get-content" not in devices
    assert "start-process" not in devices
