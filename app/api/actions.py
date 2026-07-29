from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.software import get_software_service
from app.database.repositories import (
    ActionExpiredError,
    ActionNotFoundError,
    ActionStateError,
)
from app.models.actions import (
    ActionKind,
    ActionStatusResponse,
    CancelActionResponse,
    PendingActionRecord,
)
from app.services.action_service import ActionService, ActionTaskManager
from app.services.software_service import SoftwareService


router = APIRouter(prefix="/api/actions", tags=["actions"])
action_task_manager = ActionTaskManager()


def get_action_service(
    software: SoftwareService = Depends(get_software_service),
) -> ActionService:

    async def verify(record: PendingActionRecord) -> bool:
        if record.kind is ActionKind.SOFTWARE_INSTALL:
            return (await software.check(record.resource_id)).installed
        if record.kind is ActionKind.SOFTWARE_UNINSTALL:
            return not (await software.check(record.resource_id)).installed
        return True

    return ActionService(
        software.repository,
        software.registry,
        software.runner,
        action_task_manager,
        verifier=verify,
    )


def _action_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ActionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ActionExpiredError):
        return HTTPException(status_code=410, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@router.get("", response_model=list[ActionStatusResponse])
def list_actions(
    limit: int = Query(default=30, ge=1, le=100),
    service: ActionService = Depends(get_action_service),
) -> list[ActionStatusResponse]:
    return service.list_recent(limit)


@router.get("/{action_id}/status", response_model=ActionStatusResponse)
def action_status(
    action_id: str,
    service: ActionService = Depends(get_action_service),
) -> ActionStatusResponse:
    try:
        return service.get_status(action_id)
    except ActionNotFoundError as exc:
        raise _action_http_error(exc) from exc


@router.post("/{action_id}/confirm", response_model=ActionStatusResponse, status_code=202)
async def confirm_action(
    action_id: str,
    service: ActionService = Depends(get_action_service),
) -> ActionStatusResponse:
    try:
        return service.confirm(action_id)
    except (ActionNotFoundError, ActionExpiredError, ActionStateError, ValueError) as exc:
        raise _action_http_error(exc) from exc


@router.post("/{action_id}/cancel", response_model=CancelActionResponse)
def cancel_action(
    action_id: str,
    service: ActionService = Depends(get_action_service),
) -> CancelActionResponse:
    try:
        return service.cancel(action_id)
    except (ActionNotFoundError, ActionExpiredError, ActionStateError) as exc:
        raise _action_http_error(exc) from exc
