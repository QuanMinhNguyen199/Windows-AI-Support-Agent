import asyncio

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.database.repositories import PendingActionRepository
from app.models.actions import (
    ActionKind,
    ActionExecutionResponse,
    CancelActionResponse,
)
from app.models.command import CommandResult
from app.models.software import (
    SoftwareCheckResponse,
    SoftwareInventoryItem,
    SoftwareInventoryResponse,
    SoftwareInstallResponse,
    SoftwareSummary,
)
from app.parsers.winget_parser import extract_version, winget_reports_installed
from app.services.software_catalog import SoftwareCatalog


def registry_from_catalog(catalog: SoftwareCatalog) -> CommandRegistry:
    entries = catalog.entries
    return CommandRegistry(
        software_commands={
            software_id: entry.check_commands
            for software_id, entry in entries.items()
        },
        software_packages={
            software_id: entry.winget_id for software_id, entry in entries.items()
        },
    )


class SoftwareService:
    def __init__(
        self,
        repository: PendingActionRepository,
        *,
        catalog: SoftwareCatalog | None = None,
        registry: CommandRegistry | None = None,
        runner: CommandRunner | None = None,
    ) -> None:
        self.catalog = catalog or SoftwareCatalog()
        self.registry = registry or registry_from_catalog(self.catalog)
        self.runner = runner or CommandRunner(registry=self.registry)
        self.repository = repository

    def list_software(self) -> list[SoftwareSummary]:
        return self.catalog.list()

    async def scan_inventory(self) -> SoftwareInventoryResponse:
        summaries = self.list_software()
        winget_inventory = await self.runner.run(
            self.registry.get("software.inventory.winget_list")
        )
        semaphore = asyncio.Semaphore(6)

        async def direct_results(software_id: str) -> list[CommandResult]:
            definitions = [
                definition
                for definition in self.registry.software_checks(software_id)
                if definition.executable.casefold() != "winget"
            ]

            async def limited_run(definition):
                async with semaphore:
                    return await self.runner.run(definition)

            return await asyncio.gather(*(limited_run(item) for item in definitions))

        direct_by_software = await asyncio.gather(
            *(direct_results(item.id) for item in summaries)
        )
        checks: list[SoftwareCheckResponse] = []
        for summary, direct in zip(summaries, direct_by_software, strict=True):
            entry = self.catalog.get(summary.id)
            installed, version = self._interpret_check(
                entry.winget_id, [winget_inventory, *direct]
            )
            checks.append(
                SoftwareCheckResponse(
                    software=summary,
                    installed=installed,
                    version=version,
                    conclusion=(
                        f"{summary.display_name} đã được phát hiện."
                        if installed
                        else f"Chưa phát hiện {summary.display_name}."
                    ),
                    results=[winget_inventory, *direct],
                )
            )
        items = [
            SoftwareInventoryItem(
                software=check.software,
                installed=check.installed,
                version=check.version,
                status=(
                    f"Đã cài{f' · {check.version}' if check.version else ''}"
                    if check.installed
                    else "Chưa cài"
                ),
            )
            for check in checks
        ]
        return SoftwareInventoryResponse(
            items=items,
            scanned_count=len(items),
            message=f"Đã quét trạng thái {len(items)} ứng dụng trong catalog.",
        )

    async def check(self, software_id: str) -> SoftwareCheckResponse:
        normalized = software_id.strip().casefold()
        entry = self.catalog.get(normalized)
        summary = self.catalog.summary(normalized)
        definitions = self.registry.software_checks(normalized)
        results = await asyncio.gather(
            *(self.runner.run(definition) for definition in definitions)
        )
        installed, version = self._interpret_check(entry.winget_id, results)
        conclusion = (
            f"{entry.display_name} đã được phát hiện"
            + (f", phiên bản {version}." if version else ".")
            if installed
            else (
                f"Chưa phát hiện {entry.display_name}. "
                "Kết quả này dựa trên các command kiểm tra trong catalog."
            )
        )
        return SoftwareCheckResponse(
            software=summary,
            installed=installed,
            version=version,
            conclusion=conclusion,
            results=results,
        )

    async def request_install(self, software_id: str) -> SoftwareInstallResponse:
        normalized = software_id.strip().casefold()
        summary = self.catalog.summary(normalized)
        check = await self.check(normalized)
        if check.installed:
            return SoftwareInstallResponse(
                software=summary,
                already_installed=True,
                message=f"{summary.display_name} đã được cài; không tạo hành động mới.",
                check=check,
            )
        definition = self.registry.software_install(normalized)
        warning = (
            f"Bạn sắp cài {summary.display_name} ({summary.winget_id}) bằng winget. "
            "Hãy kiểm tra package ID và đóng ứng dụng liên quan trước khi xác nhận."
        )
        record = self.repository.create(
            resource_id=normalized,
            definition=definition,
            warning=warning,
        )
        return SoftwareInstallResponse(
            software=summary,
            already_installed=False,
            message="Đã tạo pending action; chưa có command cài đặt nào được chạy.",
            check=check,
            pending_action=self.repository.public(record),
        )

    async def request_uninstall(self, software_id: str) -> SoftwareInstallResponse:
        normalized = software_id.strip().casefold()
        summary = self.catalog.summary(normalized)
        check = await self.check(normalized)
        if not check.installed:
            return SoftwareInstallResponse(
                software=summary,
                already_installed=False,
                message=f"Không phát hiện {summary.display_name}; không cần gỡ.",
                check=check,
            )
        definition = self.registry.software_uninstall(normalized)
        record = self.repository.create(
            resource_id=normalized,
            kind=ActionKind.SOFTWARE_UNINSTALL,
            definition=definition,
            warning=(
                f"Bạn sắp gỡ {summary.display_name} ({summary.winget_id}). "
                "Dữ liệu hoặc thiết lập riêng của ứng dụng có thể vẫn còn."
            ),
        )
        return SoftwareInstallResponse(
            software=summary,
            already_installed=True,
            message="Đã tạo yêu cầu gỡ; chưa có command nào được chạy.",
            check=check,
            pending_action=self.repository.public(record),
        )

    async def confirm(self, action_id: str) -> ActionExecutionResponse:
        preview = self.repository.get(action_id)
        expected = self.registry.software_install(preview.resource_id)
        if preview.definition != expected or preview.command_id != expected.id:
            raise ValueError("Command snapshot không khớp software catalog hiện tại.")
        claimed = self.repository.claim_for_confirmation(action_id)
        if claimed.definition != expected:
            raise ValueError("Command snapshot đã thay đổi trong lúc xác nhận.")
        result = await self.runner.run(claimed.definition, confirmed=True)
        finished = self.repository.finish(action_id, result)
        message = (
            "Cài đặt hoàn tất thành công."
            if result.success
            else "Command cài đặt đã chạy nhưng không hoàn tất thành công."
        )
        return ActionExecutionResponse(
            action=self.repository.public(finished),
            result=result,
            message=message,
        )

    def cancel(self, action_id: str) -> CancelActionResponse:
        cancelled = self.repository.cancel(action_id)
        return CancelActionResponse(
            action=self.repository.public(cancelled),
            message="Đã hủy pending action; không có command nào được chạy.",
        )

    @staticmethod
    def _interpret_check(
        package_id: str, results: list[CommandResult]
    ) -> tuple[bool, str | None]:
        installed = False
        version: str | None = None
        for result in results:
            if not result.success:
                continue
            if result.executable.casefold() == "winget":
                if winget_reports_installed(result.stdout, package_id):
                    installed = True
                    version = version or extract_version(result.stdout, package_id)
            elif result.stdout.strip():
                installed = True
                version = version or extract_version(result.stdout)
        return installed, version
