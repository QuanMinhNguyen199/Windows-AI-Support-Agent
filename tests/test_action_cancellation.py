import asyncio

from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.models.command import CommandResult
from app.services.action_service import ActionService, ActionTaskManager
from app.services.software_catalog import SoftwareCatalog
from app.services.software_service import registry_from_catalog


class BlockingRunner:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.cancelled = False

    async def run(self, definition, *, confirmed=False):
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


def test_running_installer_can_be_cancelled(tmp_path) -> None:
    async def scenario():
        database = Database(tmp_path / "cancel.db")
        database.initialize()
        repository = PendingActionRepository(database)
        registry = registry_from_catalog(SoftwareCatalog())
        runner = BlockingRunner()
        tasks = ActionTaskManager()
        service = ActionService(repository, registry, runner, tasks)
        record = repository.create(
            resource_id="firefox",
            definition=registry.software_install("firefox"),
            warning="Confirm install.",
        )

        confirmed = service.confirm(record.id)
        await runner.started.wait()
        cancelling = service.cancel(record.id)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        final = service.get_status(record.id)

        assert confirmed.action.state == "executing"
        assert cancelling.action.state == "cancelling"
        assert runner.cancelled is True
        assert final.action.state == "cancelled"
        assert final.indeterminate is False

    asyncio.run(scenario())


def test_successful_install_is_not_failed_by_inconclusive_verification(tmp_path) -> None:
    async def scenario():
        database = Database(tmp_path / "verification.db")
        database.initialize()
        repository = PendingActionRepository(database)
        registry = registry_from_catalog(SoftwareCatalog())
        tasks = ActionTaskManager()

        class SuccessfulRunner:
            async def run(self, definition, *, confirmed=False):
                return CommandResult(
                    command_id=definition.id,
                    executable=definition.executable,
                    arguments=list(definition.arguments),
                    exit_code=0,
                    stdout="Successfully installed",
                    stderr="",
                    duration_ms=1,
                    timed_out=False,
                    success=True,
                )

        runner = SuccessfulRunner()

        service = ActionService(
            repository,
            registry,
            runner,
            tasks,
            verifier=lambda _: asyncio.sleep(0, result=False),
        )
        record = repository.create(
            resource_id="firefox",
            definition=registry.software_install("firefox"),
            warning="Confirm install.",
        )

        service.confirm(record.id)
        for _ in range(5):
            await asyncio.sleep(0)
            status = service.get_status(record.id)
            if not status.indeterminate:
                break

        assert status.action.state == "completed"
        assert "chưa xác minh" in status.message

    asyncio.run(scenario())
