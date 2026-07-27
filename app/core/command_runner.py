import asyncio
import locale
import re
import subprocess
import time

from app.core.command_registry import CommandRegistry
from app.core.risk_policy import RiskPolicy
from app.models.command import CommandDefinition, CommandResult


_MAC_ADDRESS = re.compile(r"(?i)\b(?:[0-9a-f]{2}[-:]){5}[0-9a-f]{2}\b")
_WINDOWS_USER_PATH = re.compile(r"(?i)([a-z]:\\users\\)[^\\\r\n]+")


class CommandRunner:
    def __init__(
        self,
        *,
        policy: RiskPolicy | None = None,
        max_output_chars: int = 16_000,
    ) -> None:
        self._policy = policy or RiskPolicy()
        self._registry = CommandRegistry()
        self._max_output_chars = max(256, max_output_chars)

    async def run(
        self,
        definition: CommandDefinition,
        *,
        confirmed: bool = False,
    ) -> CommandResult:
        self._validate(definition, confirmed=confirmed)
        return await asyncio.to_thread(self._run_sync, definition)

    def _validate(self, definition: CommandDefinition, *, confirmed: bool) -> None:
        if definition.executable.casefold() not in CommandRegistry.ALLOWED_EXECUTABLES:
            raise ValueError(f"Executable không được phép: {definition.executable}")
        self._registry.assert_registered(definition)
        self._policy.assert_can_run(definition, confirmed=confirmed)
        if any("\x00" in argument for argument in definition.arguments):
            raise ValueError("Command argument chứa ký tự không hợp lệ.")

    def _run_sync(self, definition: CommandDefinition) -> CommandResult:
        started = time.perf_counter()
        exit_code: int | None = None
        stdout_bytes = b""
        stderr_bytes = b""
        timed_out = False

        try:
            completed = subprocess.run(
                definition.argv,
                shell=False,
                capture_output=True,
                timeout=definition.timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            exit_code = completed.returncode
            stdout_bytes = completed.stdout or b""
            stderr_bytes = completed.stderr or b""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout_bytes = self._as_bytes(exc.stdout)
            stderr_bytes = self._as_bytes(exc.stderr)
            stderr_bytes += b"\nCommand timed out."
        except FileNotFoundError:
            stderr_bytes = b"Executable was not found."
        except PermissionError:
            stderr_bytes = b"Permission denied while starting executable."
        except OSError as exc:
            stderr_bytes = f"Unable to start executable: {exc}".encode(
                "utf-8", errors="replace"
            )

        duration_ms = round((time.perf_counter() - started) * 1000)
        stdout = self._sanitize(self._decode(stdout_bytes))
        stderr = self._sanitize(self._decode(stderr_bytes))
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=exit_code,
            stdout=self._limit(stdout),
            stderr=self._limit(stderr),
            duration_ms=duration_ms,
            timed_out=timed_out,
            success=exit_code == 0 and not timed_out,
        )

    @staticmethod
    def _as_bytes(value: bytes | str | None) -> bytes:
        if value is None:
            return b""
        if isinstance(value, bytes):
            return value
        return value.encode("utf-8", errors="replace")

    @staticmethod
    def _decode(value: bytes) -> str:
        encoding = locale.getpreferredencoding(False) or "utf-8"
        try:
            return value.decode(encoding, errors="replace")
        except LookupError:
            return value.decode("utf-8", errors="replace")

    def _limit(self, value: str) -> str:
        if len(value) <= self._max_output_chars:
            return value.strip()
        marker = "\n… [output đã được rút gọn]"
        return value[: self._max_output_chars - len(marker)].rstrip() + marker

    @staticmethod
    def _sanitize(value: str) -> str:
        value = _MAC_ADDRESS.sub("[MAC_REDACTED]", value)
        return _WINDOWS_USER_PATH.sub(r"\1[USER]", value)
