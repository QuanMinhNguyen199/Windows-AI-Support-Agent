from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.command import CommandResult
from app.models.actions import PendingAction


class SoftwareCategory(StrEnum):
    STUDENT = "student"
    BROWSERS = "browsers"
    OFFICE_PDF = "office_pdf"
    UTILITIES = "utilities"
    MEDIA = "media"
    ENTERTAINMENT = "entertainment"
    DEVELOPER_TOOLS = "developer_tools"


class SoftwareAudience(StrEnum):
    GENERAL = "general"
    ADVANCED = "advanced"


class SoftwareAdvancedGroup(StrEnum):
    DEVELOPER = "developer"
    MARKETING = "marketing"
    OFFICE = "office"
    SYSTEM = "system"


class SoftwareEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    display_name: str = Field(min_length=1)
    description: str = Field(min_length=3, max_length=120)
    publisher: str = Field(min_length=1)
    category: SoftwareCategory
    audience: SoftwareAudience
    advanced_group: SoftwareAdvancedGroup | None = None
    display_rank: int = Field(default=1000, ge=1, le=1000)
    winget_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._+-]+$")
    check_commands: tuple[tuple[str, ...], ...] = Field(min_length=1)
    verification_commands: tuple[tuple[str, ...], ...] = ()
    uninstall_command: tuple[str, ...] | None = None
    cleanup_paths: tuple[str, ...] = ()
    cleanup_registry_keys: tuple[str, ...] = ()
    provenance: str = Field(pattern=r"^https://github\.com/microsoft/winget-pkgs/")
    license_note: str = Field(min_length=1)

    @field_validator("check_commands", "verification_commands")
    @classmethod
    def validate_commands(
        cls, commands: tuple[tuple[str, ...], ...]
    ) -> tuple[tuple[str, ...], ...]:
        if any(not command or any(not value or "\x00" in value for value in command) for command in commands):
            raise ValueError("check_commands chứa command hoặc argument không hợp lệ")
        return commands

    @field_validator("uninstall_command")
    @classmethod
    def validate_uninstall_command(
        cls, command: tuple[str, ...] | None
    ) -> tuple[str, ...] | None:
        if command is not None and (
            not command or any(not value or "\x00" in value for value in command)
        ):
            raise ValueError("uninstall_command không hợp lệ")
        return command

    @field_validator("cleanup_paths")
    @classmethod
    def validate_cleanup_paths(cls, paths: tuple[str, ...]) -> tuple[str, ...]:
        allowed = ("%APPDATA%\\", "%LOCALAPPDATA%\\")
        for path in paths:
            normalized = path.upper()
            if not normalized.startswith(allowed) or len(path.split("\\")) < 3:
                raise ValueError("cleanup_paths chỉ được nằm trong AppData của ứng dụng")
        return paths

    @field_validator("cleanup_registry_keys")
    @classmethod
    def validate_cleanup_registry_keys(cls, keys: tuple[str, ...]) -> tuple[str, ...]:
        if any(not key.casefold().startswith("hkcu:\\software\\") for key in keys):
            raise ValueError("cleanup_registry_keys chỉ được nằm trong HKCU\\Software")
        return keys


class SoftwareCatalogFile(BaseModel):
    catalog_version: str = Field(pattern=r"^\d{4}\.\d{2}\.\d+$")
    software: dict[str, SoftwareEntry]

    @field_validator("software")
    @classmethod
    def validate_catalog(
        cls, software: dict[str, SoftwareEntry]
    ) -> dict[str, SoftwareEntry]:
        ids = list(software)
        if any(not software_id.replace("-", "").isalnum() for software_id in ids):
            raise ValueError("Software ID chỉ được chứa chữ, số và dấu gạch ngang")
        package_ids = [entry.winget_id.casefold() for entry in software.values()]
        if len(package_ids) != len(set(package_ids)):
            raise ValueError("Catalog có winget ID trùng")
        return software


class SoftwareSummary(BaseModel):
    id: str
    display_name: str
    description: str
    publisher: str
    category: SoftwareCategory
    audience: SoftwareAudience
    advanced_group: SoftwareAdvancedGroup | None = None
    display_rank: int = Field(default=1000, ge=1, le=1000)
    winget_id: str
    license_note: str
    cleanup_available: bool = False


class SoftwareCheckResponse(BaseModel):
    software: SoftwareSummary
    installed: bool
    version: str | None = None
    conclusion: str
    results: list[CommandResult]


class SoftwareRequest(BaseModel):
    software_id: str = Field(min_length=1, max_length=64)


class SoftwareInstallResponse(BaseModel):
    software: SoftwareSummary
    already_installed: bool
    message: str
    check: SoftwareCheckResponse
    pending_action: PendingAction | None = None


class SoftwareInventoryItem(BaseModel):
    software: SoftwareSummary
    installed: bool
    version: str | None = None
    status: str


class SoftwareInventoryResponse(BaseModel):
    items: list[SoftwareInventoryItem]
    scanned_count: int
    message: str
