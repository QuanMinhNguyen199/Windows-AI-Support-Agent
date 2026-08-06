import asyncio
import json

from app.core.command_registry import CommandRegistry
from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.models.command import CommandDefinition, CommandResult
from app.services.cleanup_service import CleanupService


class FakeCleanupRunner:
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult:
        count = 2 if definition.id.endswith("user_temp") else 0
        stdout = json.dumps({"file_count": count, "bytes": count * 1024})
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_ms=1,
            timed_out=False,
            success=True,
        )


class FailedCleanupRunner:
    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult:
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=1,
            stdout="",
            stderr="PowerShell error",
            duration_ms=1,
            timed_out=False,
            success=False,
        )


def make_service(tmp_path) -> CleanupService:
    database = Database(tmp_path / "cleanup.db")
    database.initialize()
    return CleanupService(
        PendingActionRepository(database), CommandRegistry(), FakeCleanupRunner()
    )


def test_scan_reports_only_reviewed_categories(tmp_path) -> None:
    response = asyncio.run(make_service(tmp_path).scan())

    assert {item.id for item in response.categories} == {
        "user_temp", "thumbnail_cache", "crash_dumps"
    }
    assert response.total_bytes == 2048
    assert all(item.selected_by_default is False for item in response.categories)


def test_cleanup_request_stays_pending_until_confirmation(tmp_path) -> None:
    response = make_service(tmp_path).request(["user_temp", "thumbnail_cache"])

    assert response.pending_action.kind == "system_cleanup"
    assert response.pending_action.state == "pending"
    assert "Downloads" in response.pending_action.warning


def test_scan_failure_is_not_reported_as_empty_machine(tmp_path) -> None:
    database = Database(tmp_path / "cleanup-failed.db")
    database.initialize()
    service = CleanupService(
        PendingActionRepository(database), CommandRegistry(), FailedCleanupRunner()
    )

    try:
        asyncio.run(service.scan())
    except RuntimeError as exc:
        assert "không đọc được file tạm" in str(exc)
    else:
        raise AssertionError("Lỗi quét không được phép biến thành kết quả 0")
