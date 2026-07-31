from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.models.command import CommandDefinition, CommandResult, RiskLevel


class ActionState(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ActionKind(StrEnum):
    SOFTWARE_INSTALL = "software_install"
    SOFTWARE_UNINSTALL = "software_uninstall"
    NETWORK_REPAIR = "network_repair"


class ActionStage(StrEnum):
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    PREPARING = "preparing"
    RUNNING = "running"
    VERIFYING = "verifying"
    CANCELLING = "cancelling"
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
    kind: ActionKind = ActionKind.SOFTWARE_INSTALL
    resource_id: str
    stage: ActionStage = ActionStage.AWAITING_CONFIRMATION
    status_message: str
    created_at: datetime


class PendingActionRecord(PendingAction):
    definition: CommandDefinition
    result: CommandResult | None = None


class ActionStatusResponse(BaseModel):
    action: PendingAction
    result: CommandResult | None = None
    message: str
    indeterminate: bool = False


class ActionExecutionResponse(ActionStatusResponse):
    """Backward-compatible alias for clients using the phase 5 schema name."""


class CancelActionResponse(BaseModel):
    action: PendingAction
    message: str
