import asyncio
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


Verifier = Callable[[PendingActionRecord], Awaitable[bool]]


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
        cancelled = self.repository.cancel(action_id)
        return CancelActionResponse(
            action=self.repository.public(cancelled),
            message="Đã hủy yêu cầu; không có command nào được chạy.",
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
                        if record.kind is ActionKind.SOFTWARE_UNINSTALL
                        else "Đang áp dụng sửa chữa mạng."
                    )
                ),
            )
            result = await self.runner.run(record.definition, confirmed=True)
            if result.success and self.verifier is not None:
                self.repository.set_verifying(record.id, "Đang xác minh kết quả.")
                verified = await self.verifier(record)
                if not verified:
                    result = result.model_copy(
                        update={
                            "success": False,
                            "stderr": (
                                f"{result.stderr}\nKhông xác minh được trạng thái "
                                "sau thao tác."
                            ).strip(),
                        }
                    )
            self.repository.finish(record.id, result)
        except asyncio.CancelledError:
            raise
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
            try:
                self.repository.finish(record.id, result)
            except Exception:
                pass

    def _response(self, record: PendingActionRecord) -> ActionStatusResponse:
        return ActionStatusResponse(
            action=self.repository.public(record),
            result=record.result,
            message=record.status_message,
            indeterminate=record.state is ActionState.EXECUTING,
        )
