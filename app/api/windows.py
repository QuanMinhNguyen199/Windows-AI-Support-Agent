from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.models.windows_support import (
    WindowsActionResponse,
    WindowsCapability,
    WindowsOverviewResponse,
    WindowsUpdateRequestResponse,
)
from app.services.windows_support_service import WindowsSupportService


router = APIRouter(prefix="/api/windows", tags=["windows"])


@lru_cache
def get_windows_support_service() -> WindowsSupportService:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    return WindowsSupportService(repository=PendingActionRepository(database))


@router.get("/capabilities", response_model=list[dict[str, str]])
def list_capabilities(
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> list[dict[str, str]]:
    return service.list_capabilities()


@router.post("/overview", response_model=WindowsOverviewResponse)
async def windows_overview(
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> WindowsOverviewResponse:
    return await service.overview()


@router.post("/update/open", response_model=WindowsActionResponse)
async def open_windows_update(
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> WindowsActionResponse:
    return await service.open_update_settings()


@router.post("/update/install", response_model=WindowsUpdateRequestResponse)
def install_windows_updates(
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> WindowsUpdateRequestResponse:
    return service.request_update_install()


@router.post("/{capability_id}", response_model=WindowsCapability)
async def inspect_capability(
    capability_id: str,
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> WindowsCapability:
    try:
        return await service.inspect(capability_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
