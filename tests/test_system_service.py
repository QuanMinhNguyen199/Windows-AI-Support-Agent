import asyncio
import json

from app.core.command_registry import CommandRegistry
from app.models.command import CommandResult
from app.services.system_service import SystemService


class FakeRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.definition = None

    async def run(self, definition, *, confirmed=False):
        self.definition = definition
        return self.result.model_copy(
            update={
                "command_id": definition.id,
                "executable": definition.executable,
                "arguments": list(definition.arguments),
            }
        )


def command_result(stdout: str, *, success: bool = True) -> CommandResult:
    return CommandResult(
        command_id="placeholder",
        executable="powershell",
        arguments=[],
        exit_code=0 if success else 1,
        stdout=stdout,
        stderr="",
        duration_ms=1,
        timed_out=False,
        success=success,
    )


def test_system_specs_are_parsed_and_converted_to_gigabytes() -> None:
    payload = {
        "device_name": "WIN-PC",
        "manufacturer": "Example",
        "model": "Model 1",
        "os_name": "Windows 11",
        "os_version": "10.0.26100",
        "os_build": "26100",
        "architecture": "64-bit",
        "cpu_name": "Example CPU",
        "physical_cores": 8,
        "logical_processors": 16,
        "memory_bytes": 16 * 1024**3,
        "gpu_names": "Example GPU",
        "system_drive": "C:",
        "disk_size_bytes": 512 * 1024**3,
        "disk_free_bytes": 128 * 1024**3,
    }
    runner = FakeRunner(command_result(json.dumps(payload)))
    service = SystemService(runner=runner, registry=CommandRegistry())

    response = asyncio.run(service.get_specs())

    assert response.available is True
    assert response.specs is not None
    assert response.specs.memory_gb == 16
    assert response.specs.disk_free_gb == 128
    assert response.specs.gpu_names == ["Example GPU"]
    assert runner.definition.id == "system.get_specs"
    assert runner.definition.risk_level == "READ_ONLY"


def test_system_specs_return_unavailable_on_invalid_output() -> None:
    service = SystemService(
        runner=FakeRunner(command_result("not-json")),
        registry=CommandRegistry(),
    )

    response = asyncio.run(service.get_specs())

    assert response.available is False
    assert response.specs is None
