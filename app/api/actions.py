from fastapi import APIRouter, Depends, HTTPException

from app.api.software import get_software_service
from app.database.repositories import (
    ActionExpiredError,
    ActionNotFoundError,
    ActionStateError,
)
from app.models.actions import ActionExecutionResponse, CancelActionResponse
from app.services.software_service import SoftwareService


router = APIRouter(prefix="/api/actions", tags=["actions"])


def _action_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ActionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ActionExpiredError):
        return HTTPException(status_code=410, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@router.post("/{action_id}/confirm", response_model=ActionExecutionResponse)
async def confirm_action(
    action_id: str,
    service: SoftwareService = Depends(get_software_service),
) -> ActionExecutionResponse:
    try:
        return await service.confirm(action_id)
    except (ActionNotFoundError, ActionExpiredError, ActionStateError, ValueError) as exc:
        raise _action_http_error(exc) from exc


@router.post("/{action_id}/cancel", response_model=CancelActionResponse)
def cancel_action(
    action_id: str,
    service: SoftwareService = Depends(get_software_service),
) -> CancelActionResponse:
    try:
        return service.cancel(action_id)
    except (ActionNotFoundError, ActionExpiredError, ActionStateError) as exc:
        raise _action_http_error(exc) from exc
