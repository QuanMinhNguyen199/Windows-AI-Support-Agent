import json
from typing import Protocol

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, CommandResult
from app.models.diagnostics import (
    DiagnosticStatus,
    SpeedTestResponse,
    SpeedTestResult,
)


class Runner(Protocol):
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult: ...


class SpeedTestProvider(Protocol):
    async def run_test(self) -> SpeedTestResponse: ...


class OoklaSpeedTestProvider:
    def __init__(
        self,
        runner: Runner | None = None,
        registry: CommandRegistry | None = None,
    ) -> None:
        self.registry = registry or CommandRegistry()
        self.runner = runner or CommandRunner(registry=self.registry)

    async def run_test(self) -> SpeedTestResponse:
        result = await self.runner.run(self.registry.get("network.speedtest"))
        if not result.success:
            return SpeedTestResponse(
                available=False,
                status=DiagnosticStatus.WARNING,
                message=(
                    "Chưa tìm thấy Ookla Speedtest CLI hoặc phép đo không thể chạy. "
                    "Bạn có thể cài từ Tiện ích rồi thử lại."
                ),
                install_software_id="speedtest",
                result=result,
            )
        try:
            payload = json.loads(result.stdout)
            measurement = self._parse(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return SpeedTestResponse(
                available=True,
                status=DiagnosticStatus.ERROR,
                message="Speedtest đã chạy nhưng dữ liệu trả về không hợp lệ.",
                result=result,
            )
        return SpeedTestResponse(
            available=True,
            status=DiagnosticStatus.SUCCESS,
            message="Đã hoàn tất phép đo tốc độ mạng.",
            measurement=measurement,
            result=result,
        )

    @staticmethod
    def _parse(payload: dict) -> SpeedTestResult:
        download = payload.get("download") or {}
        upload = payload.get("upload") or {}
        ping = payload.get("ping") or {}
        server = payload.get("server") or {}

        def mbps(value: object) -> float | None:
            return round(float(value) * 8 / 1_000_000, 2) if value is not None else None

        return SpeedTestResult(
            download_mbps=mbps(download.get("bandwidth")),
            upload_mbps=mbps(upload.get("bandwidth")),
            ping_ms=ping.get("latency"),
            jitter_ms=ping.get("jitter"),
            packet_loss_percent=payload.get("packetLoss"),
            server_name=server.get("name"),
            server_location=server.get("location"),
        )
