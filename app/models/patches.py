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
