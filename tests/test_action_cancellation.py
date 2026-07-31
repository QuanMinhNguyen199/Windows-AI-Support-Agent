import asyncio

from app.database.db import Database
from app.database.repositories import PendingActionRepository
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
