from pydantic import BaseModel

from app.models.actions import PendingAction


class RepairSummary(BaseModel):
    id: str
    display_name: str
    description: str
    warning: str


class RepairRequestResponse(BaseModel):
    repair: RepairSummary
    pending_action: PendingAction
    message: str
