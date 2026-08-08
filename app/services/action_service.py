import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.database.repositories import PendingActionRepository
from app.models.actions import (
    ActionKind,
    ActionState,
    ActionStatusResponse,
    CancelActionResponse,
    PendingActionRecord,
)
from app.services.action_explanations import explain_command_failure


Verifier = Callable[[PendingActionRecord], Awaitable[bool]]
logger = logging.getLogger("winassist")


class ActionTaskManager:
    """Owns background tasks for this process without moving execution into agents."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def start(self, action_id: str, work: Awaitable[None]) -> None:
        current = self._tasks.get(action_id)
        if current is not None and not current.done():
            raise RuntimeError("Action đã có task đang chạy.")
        task = asyncio.create_task(work, name=f"winassist-action-{action_id}")
        self._tasks[action_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(action_id, None))

    def cancel(self, action_id: str) -> bool:
        task = self._tasks.get(action_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        if not tasks:
            return
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()


class ActionService:
    def __init__(
        self,
        repository: PendingActionRepository,
        registry: CommandRegistry,
        runner: CommandRunner,
        task_manager: ActionTaskManager,
        *,
        verifier: Verifier | None = None,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.runner = runner
        self.task_manager = task_manager
        self.verifier = verifier

    def get_status(self, action_id: str) -> ActionStatusResponse:
        return self._response(self.repository.get(action_id))

    def list_recent(self, limit: int = 30) -> list[ActionStatusResponse]:
        return [self._response(record) for record in self.repository.list_recent(limit)]

    def confirm(self, action_id: str) -> ActionStatusResponse:
        preview = self.repository.get(action_id)
        self.registry.assert_registered(preview.definition)
        claimed = self.repository.claim_for_confirmation(action_id)
        self.registry.assert_registered(claimed.definition)
        self.task_manager.start(action_id, self._execute(claimed))
        return self._response(claimed)

    def cancel(self, action_id: str) -> CancelActionResponse:
        current = self.repository.get(action_id)
        if current.state is ActionState.PENDING:
            cancelled = self.repository.cancel(action_id)
            message = "Đã hủy yêu cầu; không có command nào được chạy."
        elif current.state in {ActionState.EXECUTING, ActionState.CANCELLING}:
            cancelling = self.repository.request_execution_cancel(action_id)
            if not self.task_manager.cancel(action_id):
                latest = self.repository.get(action_id)
                if latest.state is ActionState.CANCELLING:
                    cancelled = self.repository.finish_execution_cancel(action_id)
                else:
                    cancelled = latest
            else:
                cancelled = cancelling
            message = (
                "Đã nhận yêu cầu dừng installer. "
                "WinAssist sẽ quét lại trạng thái phần mềm sau khi tiến trình dừng."
            )
        else:
            from app.database.repositories import ActionStateError

            raise ActionStateError(
                f"Action không thể hủy ở trạng thái {current.state.value}."
            )
        return CancelActionResponse(
            action=self.repository.public(cancelled),
            message=message,
        )

    async def _execute(self, record: PendingActionRecord) -> None:
        try:
            self.repository.set_running(
                record.id,
                (
                    "Đang cài đặt phần mềm."
                    if record.kind is ActionKind.SOFTWARE_INSTALL
                    else (
                        "Đang gỡ phần mềm."
                        if record.kind in {ActionKind.SOFTWARE_UNINSTALL, ActionKind.SOFTWARE_PURGE}
                        else (
                            "Windows đang tải và cài các bản cập nhật."
                            if record.kind is ActionKind.WINDOWS_UPDATE
                            else (
                                "Đang dọn các nhóm file tạm bạn đã chọn."
                                if record.kind is ActionKind.SYSTEM_CLEANUP
                                else "Đang áp dụng sửa chữa mạng."
                            )
                        )
                    )
                ),
            )
            result = await self.runner.run(record.definition, confirmed=True)
            if self.repository.get(record.id).state is ActionState.CANCELLING:
                self.repository.finish_execution_cancel(record.id)
                return
            verification_warning: str | None = None
            if result.success and self.verifier is not None:
                self.repository.set_verifying(record.id, "Đang xác minh kết quả.")
                verified = await self.verifier(record)
                if not verified:
                    verification_warning = (
                        "Thao tác đã chạy thành công nhưng chưa xác minh được "
                        "trạng thái ứng dụng."
                    )
            if not result.success:
                logger.error(
                    "action_failed",
                    extra={
                        "action_id": record.id,
                        "action_kind": record.kind.value,
                        "command_id": record.command_id,
                        "exit_code": result.exit_code,
                        "timed_out": result.timed_out,
                        "error_detail": result.stderr[:1000],
                    },
                )
            success_message = None
            if result.success and record.kind is ActionKind.SYSTEM_CLEANUP:
                try:
                    cleanup = json.loads(result.stdout)
                    files = int(cleanup.get("files_deleted") or 0)
                    size_mb = int(cleanup.get("bytes_deleted") or 0) / (1024 * 1024)
                    success_message = (
                        f"Đã dọn {files} file tạm, giải phóng khoảng {size_mb:.1f} MB."
                    )
                except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
                    success_message = "Đã dọn xong các nhóm file tạm bạn chọn."
            if result.success and verification_warning:
                success_message = verification_warning
            self.repository.finish(record.id, result, success_message=success_message)
        except asyncio.CancelledError:
            if self.repository.get(record.id).state is ActionState.CANCELLING:
                self.repository.finish_execution_cancel(record.id)
            return
        except Exception as exc:
            # A normalized failed result keeps internal exception details out of the API.
            from app.models.command import CommandResult

            result = CommandResult(
                command_id=record.command_id,
                executable=record.definition.executable,
                arguments=list(record.definition.arguments),
                exit_code=None,
                stdout="",
                stderr=f"Không thể hoàn tất thao tác: {type(exc).__name__}",
                duration_ms=0,
                timed_out=False,
                success=False,
            )
            logger.error(
                "action_exception",
                extra={
                    "action_id": record.id,
                    "action_kind": record.kind.value,
                    "command_id": record.command_id,
                    "exception_type": type(exc).__name__,
                },
            )
            try:
                self.repository.finish(record.id, result)
            except Exception:
                pass

    def _response(self, record: PendingActionRecord) -> ActionStatusResponse:
        failure_summary, failure_suggestions = explain_command_failure(record.result)
        return ActionStatusResponse(
            action=self.repository.public(record),
            result=record.result,
            message=record.status_message,
            indeterminate=record.state in {
                ActionState.EXECUTING,
                ActionState.CANCELLING,
            },
            failure_summary=failure_summary,
            failure_suggestions=failure_suggestions,
        )
