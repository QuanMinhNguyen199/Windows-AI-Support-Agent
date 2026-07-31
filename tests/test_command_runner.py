import asyncio
import subprocess
import threading
from unittest.mock import patch

import pytest

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, RiskLevel


def test_runner_uses_argument_list_and_shell_false() -> None:
    completed = subprocess.CompletedProcess(
        args=["ipconfig"], returncode=0, stdout=b"ok", stderr=b""
    )
    with patch("app.core.command_runner.subprocess.run", return_value=completed) as run:
        result = asyncio.run(
            CommandRunner().run(CommandRegistry().get("network.ipconfig_basic"))
        )

    assert result.success is True
    assert result.stdout == "ok"
    assert run.call_args.args[0] == ["ipconfig"]
    assert run.call_args.kwargs["shell"] is False


def test_runner_handles_timeout() -> None:
    with patch(
        "app.core.command_runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["ping"], timeout=1, output=b"partial"),
    ):
        result = asyncio.run(
            CommandRunner().run(CommandRegistry().get("network.ping_public_dns"))
        )

    assert result.timed_out is True
    assert result.success is False
    assert "partial" in result.stdout


def test_runner_handles_missing_executable() -> None:
    with patch(
        "app.core.command_runner.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        result = asyncio.run(
            CommandRunner().run(CommandRegistry().get("network.ipconfig_basic"))
        )

    assert result.exit_code is None
    assert result.success is False
    assert "not found" in result.stderr.casefold()


def test_runner_rejects_executable_outside_allowlist() -> None:
    unsafe = CommandDefinition(
        id="test.unsafe",
        executable="cmd",
        arguments=("/c", "whoami"),
        risk_level=RiskLevel.READ_ONLY,
        description="Must not run.",
    )

    with pytest.raises(ValueError, match="không được phép"):
        asyncio.run(CommandRunner().run(unsafe))


def test_runner_rejects_tampered_definition_with_allowed_executable() -> None:
    tampered = CommandDefinition(
        id="network.ipconfig_basic",
        executable="ipconfig",
        arguments=("/release",),
        risk_level=RiskLevel.READ_ONLY,
        description="Disguised mutation.",
    )

    with pytest.raises(ValueError, match="không khớp registry"):
        asyncio.run(CommandRunner().run(tampered))


def test_runner_limits_and_redacts_output() -> None:
    output = (
        b"C:\\Users\\alice\\file.txt 00-11-22-33-44-55 " + b"x" * 600
    )
    completed = subprocess.CompletedProcess(
        args=["ipconfig"], returncode=0, stdout=output, stderr=b""
    )
    with patch("app.core.command_runner.subprocess.run", return_value=completed):
        result = asyncio.run(
            CommandRunner(max_output_chars=256).run(
                CommandRegistry().get("network.ipconfig_basic")
            )
        )

    assert "[USER]" in result.stdout
    assert "[MAC_REDACTED]" in result.stdout
    assert "output đã được rút gọn" in result.stdout


def test_cancelling_confirmed_low_risk_command_kills_process_tree() -> None:
    started = threading.Event()
    stopped = threading.Event()

    class FakeProcess:
        pid = 4321
        returncode = None

        def communicate(self, timeout=None):
            started.set()
            while not stopped.wait(0.01):
                pass
            self.returncode = 1
            return b"", b"cancelled"

        def poll(self):
            return self.returncode

        def terminate(self):
            stopped.set()

    fake_process = FakeProcess()

    def fake_run(argv, **kwargs):
        assert argv == ["taskkill", "/PID", "4321", "/T", "/F"]
        assert kwargs["shell"] is False
        stopped.set()
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    async def scenario():
        runner = CommandRunner()
        with (
            patch("app.core.command_runner.subprocess.Popen", return_value=fake_process),
            patch("app.core.command_runner.subprocess.run", side_effect=fake_run),
        ):
            task = asyncio.create_task(
                runner.run(
                    CommandRegistry().get("repair.flush_dns"),
                    confirmed=True,
                )
            )
            while not started.is_set():
                await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())
    assert stopped.is_set()
