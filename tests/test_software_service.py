import asyncio

import pytest

from app.database.db import Database
from app.database.repositories import ActionStateError, PendingActionRepository
from app.models.command import CommandDefinition, CommandResult
from app.services.software_catalog import SoftwareCatalog
from app.services.software_service import SoftwareService, registry_from_catalog


class FakeSoftwareRunner:
    def __init__(self, *, installed: bool = False) -> None:
        self.installed = installed
        self.calls: list[tuple[str, bool]] = []

    async def run(
        self, definition: CommandDefinition, *, confirmed: bool = False
    ) -> CommandResult:
        self.calls.append((definition.id, confirmed))
        is_install = definition.id.startswith("software.install.")
        if is_install:
            stdout = "Successfully installed"
            success = True
        elif self.installed and definition.executable == "winget":
            package_id = definition.arguments[2]
            stdout = f"Example {package_id} 128.0 winget"
            success = True
        else:
            stdout = ""
            success = False
        return CommandResult(
            command_id=definition.id,
            executable=definition.executable,
            arguments=list(definition.arguments),
            exit_code=0 if success else 1,
            stdout=stdout,
            stderr="",
            duration_ms=1,
            timed_out=False,
            success=success,
        )


def make_service(tmp_path, *, installed: bool = False):
    database = Database(tmp_path / "software.db")
    database.initialize()
    repository = PendingActionRepository(database)
    catalog = SoftwareCatalog()
    registry = registry_from_catalog(catalog)
    runner = FakeSoftwareRunner(installed=installed)
    return (
        SoftwareService(
            repository,
            catalog=catalog,
            registry=registry,
            runner=runner,
        ),
        repository,
        runner,
        database,
    )


def test_install_request_only_creates_pending_action(tmp_path) -> None:
    service, _, runner, _ = make_service(tmp_path)

    response = asyncio.run(service.request_install("firefox"))

    assert response.already_installed is False
    assert response.pending_action is not None
    assert response.pending_action.state == "pending"
    assert not any(command_id.startswith("software.install.") for command_id, _ in runner.calls)


def test_confirm_runs_saved_command_once(tmp_path) -> None:
    service, _, runner, _ = make_service(tmp_path)
    pending = asyncio.run(service.request_install("firefox")).pending_action
    assert pending is not None

    response = asyncio.run(service.confirm(pending.id))

    assert response.action.state == "completed"
    install_calls = [
        call for call in runner.calls if call[0] == "software.install.firefox"
    ]
    assert install_calls == [("software.install.firefox", True)]
    with pytest.raises(ActionStateError):
        asyncio.run(service.confirm(pending.id))


def test_installed_software_does_not_create_action(tmp_path) -> None:
    service, _, runner, _ = make_service(tmp_path, installed=True)

    response = asyncio.run(service.request_install("firefox"))

    assert response.already_installed is True
    assert response.pending_action is None
    assert not any(command_id.startswith("software.install.") for command_id, _ in runner.calls)


def test_database_command_tampering_is_rejected(tmp_path) -> None:
    service, repository, runner, database = make_service(tmp_path)
    pending = asyncio.run(service.request_install("firefox")).pending_action
    assert pending is not None
    with database.connect() as connection:
        connection.execute(
            "UPDATE pending_actions SET command_id = ? WHERE id = ?",
            ("software.install.vlc", pending.id),
        )

    with pytest.raises(ValueError, match="snapshot"):
        asyncio.run(service.confirm(pending.id))

    assert repository.get(pending.id).state == "pending"
    assert not any(command_id.startswith("software.install.") for command_id, _ in runner.calls)
