import json
from typing import Protocol

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, CommandResult
from app.models.system import SystemSpecs, SystemSpecsResponse


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

    @staticmethod
    def _parse(payload: dict) -> SystemSpecs:
        def gigabytes(value: object) -> float | None:
            if value is None:
                return None
            return round(float(value) / (1024**3), 1)

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
