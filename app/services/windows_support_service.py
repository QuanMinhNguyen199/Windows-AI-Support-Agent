import asyncio
import json
from typing import Any, Protocol

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, CommandResult
from app.models.windows_support import (
    CapabilityState,
    WindowsCapability,
    WindowsOverviewResponse,
)


class Runner(Protocol):
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult: ...


_CAPABILITIES = {
    "battery": ("Pin", "windows.battery"),
    "storage": ("Dung lượng", "windows.storage"),
    "devices": ("Thiết bị âm thanh, camera và Bluetooth", "windows.devices"),
    "printers": ("Máy in", "windows.printers"),
    "update": ("Windows Update", "windows.update_status"),
    "datetime": ("Ngày giờ và múi giờ", "windows.datetime"),
    "startup": ("Ứng dụng khởi động", "windows.startup_apps"),
}


class WindowsSupportService:
    def __init__(
        self,
        runner: Runner | None = None,
        registry: CommandRegistry | None = None,
    ) -> None:
        self.registry = registry or CommandRegistry()
        self.runner = runner or CommandRunner(registry=self.registry)

    def list_capabilities(self) -> list[dict[str, str]]:
        return [
            {"id": capability_id, "title": title}
            for capability_id, (title, _) in _CAPABILITIES.items()
        ]

    async def inspect(self, capability_id: str) -> WindowsCapability:
        normalized = capability_id.strip().casefold()
        try:
            title, command_id = _CAPABILITIES[normalized]
        except KeyError as exc:
            raise ValueError("Capability Windows không được hỗ trợ.") from exc
        result = await self.runner.run(self.registry.get(command_id))
        if not result.success:
            return WindowsCapability(
                id=normalized,
                title=title,
                state=CapabilityState.ERROR,
                summary="Không đủ dữ liệu để kiểm tra capability này.",
                recommendations=["Thử chạy lại hoặc kiểm tra phiên bản Windows."],
            )
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            return WindowsCapability(
                id=normalized,
                title=title,
                state=CapabilityState.ERROR,
                summary="Windows trả về dữ liệu không hợp lệ.",
            )
        return self._analyze(normalized, title, payload)

    async def overview(self) -> WindowsOverviewResponse:
        results = await asyncio.gather(
            *(self.inspect(capability_id) for capability_id in _CAPABILITIES)
        )
        available = sum(
            item.state is CapabilityState.AVAILABLE for item in results
        )
        warnings = sum(
            item.state in {CapabilityState.WARNING, CapabilityState.ERROR}
            for item in results
        )
        return WindowsOverviewResponse(
            capabilities=results,
            available_count=available,
            warning_count=warnings,
            message=f"Đã kiểm tra {len(results)} nhóm hỗ trợ Windows.",
        )

    def _analyze(
        self, capability_id: str, title: str, payload: dict[str, Any]
    ) -> WindowsCapability:
        if not payload.get("supported", False):
            return WindowsCapability(
                id=capability_id,
                title=title,
                state=CapabilityState.UNAVAILABLE,
                summary="Thiết bị hoặc capability này không có trên máy.",
                data=self._safe_data(capability_id, payload),
            )
        data = self._safe_data(capability_id, payload)
        state = CapabilityState.AVAILABLE
        summary = "Không phát hiện cảnh báo cơ bản."
        recommendations: list[str] = []

        if capability_id == "battery":
            batteries = data.get("batteries", [])
            levels = [
                item.get("EstimatedChargeRemaining")
                for item in batteries
                if isinstance(item, dict)
                and isinstance(item.get("EstimatedChargeRemaining"), int)
            ]
            summary = (
                f"Pin hiện ở mức {min(levels)}%."
                if levels
                else "Có pin nhưng chưa đọc được mức sạc."
            )
        elif capability_id == "storage":
            drives = data.get("drives", [])
            low = [
                item
                for item in drives
                if isinstance(item, dict)
                and item.get("Size")
                and item.get("FreeSpace") is not None
                and item["FreeSpace"] / item["Size"] < 0.1
            ]
            summary = f"Đã phát hiện {len(drives)} ổ đĩa cục bộ."
            if low:
                state = CapabilityState.WARNING
                summary = f"{len(low)} ổ đĩa còn dưới 10% dung lượng trống."
                recommendations.append("Dọn dung lượng thủ công sau khi kiểm tra file.")
        elif capability_id == "devices":
            devices = data.get("devices", [])
            errors = [
                item for item in devices
                if isinstance(item, dict)
                and str(item.get("Status", "")).casefold() not in {"ok", "unknown"}
            ]
            summary = f"Đã phát hiện {len(devices)} thiết bị liên quan."
            if errors:
                state = CapabilityState.WARNING
                summary = f"{len(errors)} thiết bị không ở trạng thái OK."
        elif capability_id == "printers":
            printers = data.get("printers", [])
            jobs = sum(
                int(item.get("JobCount") or 0)
                for item in printers if isinstance(item, dict)
            )
            summary = f"Đã phát hiện {len(printers)} máy in và {jobs} print job."
        elif capability_id == "update":
            summary = "Đã đọc trạng thái Windows Update và bản vá gần nhất."
            if data.get("reboot_pending"):
                state = CapabilityState.WARNING
                summary = "Windows đang chờ khởi động lại để hoàn tất cập nhật."
                recommendations.append("Lưu công việc trước khi tự khởi động lại máy.")
        elif capability_id == "datetime":
            summary = (
                f"Múi giờ hiện tại: {data.get('timezone_name') or 'không xác định'}."
            )
        elif capability_id == "startup":
            summary = (
                f"Có {len(data.get('apps', []))} ứng dụng được ghi nhận khi khởi động."
            )
        return WindowsCapability(
            id=capability_id,
            title=title,
            state=state,
            summary=summary,
            data=data,
            recommendations=recommendations,
        )

    @staticmethod
    def _safe_data(capability_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "battery": {"supported", "batteries"},
            "storage": {"supported", "drives"},
            "devices": {"supported", "devices"},
            "printers": {"supported", "printers"},
            "update": {
                "supported", "service_status", "start_type",
                "reboot_pending", "latest_hotfix",
            },
            "datetime": {
                "supported", "local_time", "timezone_id",
                "timezone_name", "utc_offset",
            },
            "startup": {"supported", "apps"},
        }[capability_id]
        return {key: value for key, value in payload.items() if key in allowed}
