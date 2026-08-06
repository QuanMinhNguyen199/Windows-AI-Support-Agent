from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    HIGH_RISK = "HIGH_RISK"


class CommandDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=3, pattern=r"^[a-z][a-z0-9_.-]+$")
    executable: str = Field(min_length=1)
    arguments: tuple[str, ...] = ()
    risk_level: RiskLevel
    requires_admin: bool = False
    timeout_seconds: int = Field(default=20, ge=1, le=3600)
    description: str = Field(min_length=1)

    @property
    def argv(self) -> list[str]:
        return [self.executable, *self.arguments]

    @property
    def display_command(self) -> str:
        def quote(value: str) -> str:
            return f'"{value}"' if any(char.isspace() for char in value) else value

        return " ".join(quote(value) for value in self.argv)


class CommandResult(BaseModel):
    command_id: str
    executable: str
    arguments: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
    success: bool
