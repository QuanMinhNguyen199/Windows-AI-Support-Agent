from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.command import CommandResult
from app.models.actions import PendingAction


class SoftwareCategory(StrEnum):
    BROWSERS = "browsers"
    OFFICE_PDF = "office_pdf"
    UTILITIES = "utilities"
    MEDIA = "media"
    DEVELOPER_TOOLS = "developer_tools"


class SoftwareEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    display_name: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    category: SoftwareCategory
    winget_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._+-]+$")
    check_commands: tuple[tuple[str, ...], ...] = Field(min_length=1)
    provenance: str = Field(pattern=r"^https://github\.com/microsoft/winget-pkgs/")
    license_note: str = Field(min_length=1)

    @field_validator("check_commands")
    @classmethod
    def validate_commands(
        cls, commands: tuple[tuple[str, ...], ...]
    ) -> tuple[tuple[str, ...], ...]:
        if any(not command or any(not value or "\x00" in value for value in command) for command in commands):
            raise ValueError("check_commands chứa command hoặc argument không hợp lệ")
        return commands


class SoftwareCatalogFile(BaseModel):
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
    publisher: str
    category: SoftwareCategory
    winget_id: str
    license_note: str


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
