from fastapi import APIRouter, Depends, HTTPException

from app.api.software import get_software_service
from app.models.cleanup import CleanupRequest, CleanupRequestResponse, CleanupScanResponse
from app.services.cleanup_service import CleanupService
from app.services.software_service import SoftwareService


router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])


def get_cleanup_service(
    software: SoftwareService = Depends(get_software_service),
) -> CleanupService:
    return CleanupService(software.repository, software.registry, software.runner)


@router.post("/scan", response_model=CleanupScanResponse)
async def scan_cleanup(
    service: CleanupService = Depends(get_cleanup_service),
) -> CleanupScanResponse:
    return await service.scan()


@router.post("/request", response_model=CleanupRequestResponse)
def request_cleanup(
    request: CleanupRequest,
    service: CleanupService = Depends(get_cleanup_service),
) -> CleanupRequestResponse:
    try:
        return service.request(request.categories)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
