from pydantic import BaseModel, Field

from app.models.actions import PendingAction


class CleanupCategory(BaseModel):
    id: str
    title: str
    description: str
    file_count: int = 0
    bytes: int = 0
    selected_by_default: bool = False


class CleanupScanResponse(BaseModel):
    categories: list[CleanupCategory]
    total_bytes: int
    message: str


class CleanupRequest(BaseModel):
    categories: list[str] = Field(min_length=1, max_length=3)


class CleanupRequestResponse(BaseModel):
    pending_action: PendingAction
    message: str
