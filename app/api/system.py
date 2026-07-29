from functools import lru_cache

from fastapi import APIRouter, Depends

from app.models.system import SystemSpecsResponse
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
