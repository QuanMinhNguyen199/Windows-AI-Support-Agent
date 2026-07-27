from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.models.command import CommandDefinition, CommandResult, RiskLevel


class ActionState(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PendingAction(BaseModel):
    id: str
    command_id: str
    display_command: str
    risk_level: RiskLevel
    warning: str
    expires_at: datetime
    state: ActionState


class PendingActionRecord(PendingAction):
    software_id: str
    definition: CommandDefinition
    created_at: datetime


class ActionExecutionResponse(BaseModel):
    action: PendingAction
    result: CommandResult
    message: str


class CancelActionResponse(BaseModel):
    action: PendingAction
    message: str
