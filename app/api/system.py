from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.models.system import (
    GraphicsAppOpenResponse,
    GraphicsDriverResponse,
    SystemSpecsResponse,
)
from app.services.system_service import SystemService

router = APIRouter(prefix="/api/system", tags=["system"])


@lru_cache
def get_system_service() -> SystemService:
    return SystemService()


@router.get("/specs", response_model=SystemSpecsResponse)
async def system_specs(
    service: SystemService = Depends(get_system_service),
) -> SystemSpecsResponse:
    return await service.get_specs()


@router.get("/graphics-driver", response_model=GraphicsDriverResponse)
async def graphics_driver(
    service: SystemService = Depends(get_system_service),
) -> GraphicsDriverResponse:
    return await service.get_graphics_driver_recommendations()


@router.post("/graphics-driver/{vendor}/open", response_model=GraphicsAppOpenResponse)
async def open_graphics_app(
    vendor: str,
    service: SystemService = Depends(get_system_service),
) -> GraphicsAppOpenResponse:
    try:
        return await service.open_graphics_app(vendor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
