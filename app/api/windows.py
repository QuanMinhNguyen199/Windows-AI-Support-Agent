from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.models.windows_support import WindowsCapability, WindowsOverviewResponse
from app.services.windows_support_service import WindowsSupportService


router = APIRouter(prefix="/api/windows", tags=["windows"])


@lru_cache
def get_windows_support_service() -> WindowsSupportService:
    return WindowsSupportService()


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


@router.post("/{capability_id}", response_model=WindowsCapability)
async def inspect_capability(
    capability_id: str,
    service: WindowsSupportService = Depends(get_windows_support_service),
) -> WindowsCapability:
    try:
        return await service.inspect(capability_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
