from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.models.command import CommandResult


class CapabilityState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    WARNING = "warning"
    ERROR = "error"


class WindowsCapability(BaseModel):
    id: str
    title: str
    state: CapabilityState
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class WindowsOverviewResponse(BaseModel):
    capabilities: list[WindowsCapability]
    available_count: int
    warning_count: int
    message: str


class WindowsActionResponse(BaseModel):
    success: bool
    message: str
    result: CommandResult
