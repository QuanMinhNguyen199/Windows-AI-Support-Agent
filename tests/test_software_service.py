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
        is_uninstall = definition.id.startswith("software.uninstall.")
        is_verification = definition.id.startswith("software.verify.")
        if is_install:
            stdout = "Successfully installed"
            success = True
            self.installed = True
        elif is_uninstall:
            stdout = "Successfully uninstalled"
            success = True
            self.installed = False
        elif is_verification and self.installed:
            stdout = r"C:\Program Files\Mozilla Firefox\firefox.exe"
            success = True
        elif (
            self.installed
            and definition.executable == "winget"
            and definition.id != "software.inventory.winget_list"
        ):
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


def test_inventory_scan_returns_status_for_every_catalog_item(tmp_path) -> None:
    service, _, _, _ = make_service(tmp_path, installed=True)

    response = asyncio.run(service.scan_inventory())

    assert response.scanned_count == len(service.list_software())
    assert len(response.items) == response.scanned_count
    assert all(
        item.status.startswith("Đã cài") or item.status == "Chưa cài"
        for item in response.items
    )
    assert {item.software.id for item in response.items} == {
        item.id for item in service.list_software()
    }


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


def test_firefox_ghost_winget_entry_is_not_treated_as_installed(tmp_path) -> None:
    service, _, runner, _ = make_service(tmp_path, installed=True)
    original_run = runner.run

    async def run_without_executable(definition, *, confirmed=False):
        if definition.id.startswith("software.verify.firefox"):
            runner.calls.append((definition.id, confirmed))
            return CommandResult(
                command_id=definition.id,
                executable=definition.executable,
                arguments=list(definition.arguments),
                exit_code=1,
                stdout="",
                stderr="Executable not found",
                duration_ms=1,
                timed_out=False,
                success=False,
            )
        return await original_run(definition, confirmed=confirmed)

    runner.run = run_without_executable

    response = asyncio.run(service.check("firefox"))

    assert response.installed is False
    assert any(
        result.executable == "winget" and result.success
        for result in response.results
    )
    assert any(
        result.command_id.startswith("software.verify.firefox")
        and not result.success
        for result in response.results
    )
