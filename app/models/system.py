from pydantic import BaseModel, Field

from app.models.command import CommandResult


class SystemSpecs(BaseModel):
    device_name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    os_build: str | None = None
    architecture: str | None = None
    cpu_name: str | None = None
    physical_cores: int | None = Field(default=None, ge=0)
    logical_processors: int | None = Field(default=None, ge=0)
    memory_gb: float | None = Field(default=None, ge=0)
    gpu_names: list[str] = Field(default_factory=list)
    system_drive: str | None = None
    disk_size_gb: float | None = Field(default=None, ge=0)
    disk_free_gb: float | None = Field(default=None, ge=0)


class SystemSpecsResponse(BaseModel):
    available: bool
    message: str
    specs: SystemSpecs | None = None
    result: CommandResult
