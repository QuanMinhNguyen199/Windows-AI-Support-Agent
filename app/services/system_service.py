import json
from typing import Protocol, cast

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, CommandResult
from app.models.system import (
    GraphicsAdapter,
    GraphicsAppOpenResponse,
    GraphicsDriverResponse,
    SystemSpecs,
    SystemSpecsResponse,
)

GRAPHICS_VENDOR_SUPPORT = {
    "nvidia": (
        "NVIDIA",
        "NVIDIA App sẽ mở cửa sổ riêng để kiểm tra và cài phiên bản phù hợp.",
        "https://www.nvidia.com/en-us/software/nvidia-app/",
    ),
    "amd": (
        "AMD",
        "AMD Software sẽ mở cửa sổ riêng để kiểm tra và cài phiên bản phù hợp.",
        "https://www.amd.com/en/support/download/drivers.html",
    ),
    "intel": (
        "Intel",
        "Intel Driver Assistant chạy trên máy nhưng tiếp tục cập nhật trong trình duyệt.",
        "https://www.intel.com/content/www/us/en/support/detect.html",
    ),
}


class Runner(Protocol):
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult: ...


class SystemService:
    def __init__(
        self,
        runner: Runner | None = None,
        registry: CommandRegistry | None = None,
    ) -> None:
        self.registry = registry or CommandRegistry()
        self.runner = runner or CommandRunner(registry=self.registry)

    async def get_specs(self) -> SystemSpecsResponse:
        result = await self.runner.run(self.registry.get("system.get_specs"))
        if not result.success:
            return SystemSpecsResponse(
                available=False,
                message="Windows không trả về được thông số máy.",
                result=result,
            )
        try:
            payload = json.loads(result.stdout)
            specs = self._parse(payload)
        except (json.JSONDecodeError, TypeError, ValueError):
            return SystemSpecsResponse(
                available=False,
                message="Dữ liệu thông số máy không hợp lệ.",
                result=result,
            )
        return SystemSpecsResponse(
            available=True,
            message="Đã đọc thông số máy.",
            specs=specs,
            result=result,
        )

    async def get_graphics_driver_recommendations(self) -> GraphicsDriverResponse:
        result = await self.runner.run(self.registry.get("system.graphics_adapters"))
        if not result.success:
            return GraphicsDriverResponse(
                available=False,
                message="Windows không đọc được thông tin card màn hình.",
                result=result,
            )
        try:
            payload = json.loads(result.stdout)
            raw_adapters = payload.get("adapters", [])
            if isinstance(raw_adapters, dict):
                raw_adapters = [raw_adapters]
            management_apps = payload.get("management_apps", {})
            adapters = [
                self._graphics_adapter(item, management_apps) for item in raw_adapters
            ]
        except (json.JSONDecodeError, TypeError, ValueError):
            adapters = []
        adapters = [adapter for adapter in adapters if adapter is not None]
        return GraphicsDriverResponse(
            available=bool(adapters),
            message=(
                "Đã tìm thấy công cụ chính hãng phù hợp."
                if adapters
                else "Chưa xác định được hãng card màn hình được hỗ trợ."
            ),
            adapters=adapters,
            result=result,
        )

    @staticmethod
    def _graphics_adapter(
        item: object, management_apps: object | None = None
    ) -> GraphicsAdapter | None:
        if not isinstance(item, dict):
            return None
        name = str(item.get("Name") or "").strip()
        device_id = str(item.get("PNPDeviceID") or "").lower()
        identity = f"{name} {device_id}".lower()
        vendor_key = next(
            (key for key in GRAPHICS_VENDOR_SUPPORT if key in identity), None
        )
        if vendor_key is None:
            return None
        vendor, recommendation, download_url = GRAPHICS_VENDOR_SUPPORT[vendor_key]
        apps = management_apps if isinstance(management_apps, dict) else {}
        return GraphicsAdapter(
            name=name or f"GPU {vendor}",
            vendor=vendor,
            driver_version=str(item.get("DriverVersion") or "").strip() or None,
            recommendation=recommendation,
            download_url=download_url,
            management_app_installed=bool(apps.get(vendor_key, False)),
        )

    async def open_graphics_app(self, vendor: str) -> GraphicsAppOpenResponse:
        normalized = vendor.strip().casefold()
        if normalized not in GRAPHICS_VENDOR_SUPPORT:
            raise ValueError("Hãng đồ họa không được hỗ trợ.")
        result = await self.runner.run(
            self.registry.get(f"system.graphics.open_{normalized}"), confirmed=True
        )
        return GraphicsAppOpenResponse(
            success=result.success,
            message=(
                (
                    "Đã mở Intel Driver Assistant. Intel sẽ tiếp tục trong trình duyệt."
                    if normalized == "intel"
                    else f"Đã mở công cụ cập nhật {GRAPHICS_VENDOR_SUPPORT[normalized][0]}."
                )
                if result.success
                else "Không mở được công cụ cập nhật. Hãy kiểm tra lại trạng thái."
            ),
            result=result,
        )

    @staticmethod
    def _parse(payload: dict) -> SystemSpecs:
        def gigabytes(value: object) -> float | None:
            if value is None:
                return None
            return round(float(cast(str | int | float, value)) / (1024**3), 1)

        gpu_value = payload.get("gpu_names")
        if isinstance(gpu_value, str):
            gpu_names = [gpu_value]
        elif isinstance(gpu_value, list):
            gpu_names = [str(item) for item in gpu_value if item]
        else:
            gpu_names = []
        return SystemSpecs(
            device_name=payload.get("device_name"),
            manufacturer=payload.get("manufacturer"),
            model=payload.get("model"),
            os_name=payload.get("os_name"),
            os_version=payload.get("os_version"),
            os_build=payload.get("os_build"),
            architecture=payload.get("architecture"),
            cpu_name=payload.get("cpu_name"),
            physical_cores=payload.get("physical_cores"),
            logical_processors=payload.get("logical_processors"),
            memory_gb=gigabytes(payload.get("memory_bytes")),
            gpu_names=gpu_names,
            system_drive=payload.get("system_drive"),
            disk_size_gb=gigabytes(payload.get("disk_size_bytes")),
            disk_free_gb=gigabytes(payload.get("disk_free_bytes")),
        )
