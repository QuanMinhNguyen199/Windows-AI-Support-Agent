from pydantic import BaseModel, Field


class PatchRelease(BaseModel):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    released_at: str
    title: str
    summary: str
    highlights: list[str]
    fixes: list[str]
    security: list[str] = Field(default_factory=list)


class PatchNotesFile(BaseModel):
    releases: list[PatchRelease] = Field(min_length=1)


class UpdateStatus(BaseModel):
    current_version: str
    latest_version: str | None = None
    update_available: bool = False
    installer_available: bool = False
    installer_url: str | None = None
    installer_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    release_url: str | None = None
    message: str
