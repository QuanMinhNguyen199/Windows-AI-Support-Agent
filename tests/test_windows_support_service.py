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


def test_open_windows_update_uses_registered_settings_command() -> None:
    service = WindowsSupportService(
        runner=FakeRunner({"windows.open_update_settings": {}}),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.open_update_settings())

    assert response.success is True
    assert response.result.command_id == "windows.open_update_settings"
    assert response.result.executable == "powershell"


def test_windows_update_stopped_manual_service_is_not_a_warning() -> None:
    service = WindowsSupportService(
        runner=FakeRunner(
            {
                "windows.update_status": {
                    "supported": True,
                    "service_status": "Stopped",
                    "start_type": "Manual",
                    "reboot_pending": False,
                    "latest_hotfix": None,
                    "update_check_succeeded": True,
                    "available_update_count": 0,
                    "available_updates": [],
                }
            }
        ),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.inspect("update"))

    assert response.state == "available"
    assert response.summary == "Máy đã cập nhật. Hiện không có bản cập nhật mới."


def test_windows_update_disabled_service_has_plain_language_warning() -> None:
    service = WindowsSupportService(
        runner=FakeRunner(
            {
                "windows.update_status": {
                    "supported": True,
                    "service_status": "Stopped",
                    "start_type": "Disabled",
                    "reboot_pending": False,
                    "latest_hotfix": None,
                    "update_check_succeeded": True,
                    "available_update_count": 0,
                    "available_updates": [],
                }
            }
        ),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.inspect("update"))

    assert response.state == "warning"
    assert response.summary == "Windows Update đang bị tắt trên máy."


def test_windows_update_reports_available_updates() -> None:
    service = WindowsSupportService(
        runner=FakeRunner(
            {
                "windows.update_status": {
                    "supported": True,
                    "service_status": "Running",
                    "start_type": "Manual",
                    "reboot_pending": False,
                    "latest_hotfix": None,
                    "update_check_succeeded": True,
                    "available_update_count": 2,
                    "available_updates": [
                        {"title": "Security Update", "kb": ["123"], "severity": "Critical"},
                        {"title": "Cumulative Update", "kb": [], "severity": None},
                    ],
                    "update_error": None,
                }
            }
        ),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.inspect("update"))

    assert response.state == "warning"
    assert response.summary == "Có 2 bản cập nhật mới đang chờ bạn xem và cài."
    assert len(response.data["available_updates"]) == 2
