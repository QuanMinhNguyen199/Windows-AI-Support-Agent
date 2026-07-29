from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.models.software import (
    SoftwareCheckResponse,
    SoftwareInstallResponse,
    SoftwareInventoryResponse,
    SoftwareRequest,
    SoftwareSummary,
)
from app.services.software_catalog import SoftwareCatalogError
from app.services.software_service import SoftwareService


router = APIRouter(prefix="/api/software", tags=["software"])


@lru_cache
def get_software_service() -> SoftwareService:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    return SoftwareService(PendingActionRepository(database))


def _catalog_error(exc: SoftwareCatalogError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.get("", response_model=list[SoftwareSummary])
def list_software(
    service: SoftwareService = Depends(get_software_service),
) -> list[SoftwareSummary]:
    return service.list_software()


@router.post("/scan", response_model=SoftwareInventoryResponse)
async def scan_software(
    service: SoftwareService = Depends(get_software_service),
) -> SoftwareInventoryResponse:
    return await service.scan_inventory()


@router.post("/check", response_model=SoftwareCheckResponse)
async def check_software(
    request: SoftwareRequest,
    service: SoftwareService = Depends(get_software_service),
) -> SoftwareCheckResponse:
    try:
        return await service.check(request.software_id)
    except SoftwareCatalogError as exc:
        raise _catalog_error(exc) from exc


@router.post("/install", response_model=SoftwareInstallResponse)
async def install_software(
    request: SoftwareRequest,
    service: SoftwareService = Depends(get_software_service),
) -> SoftwareInstallResponse:
    try:
        return await service.request_install(request.software_id)
    except SoftwareCatalogError as exc:
        raise _catalog_error(exc) from exc


@router.post("/uninstall", response_model=SoftwareInstallResponse)
async def uninstall_software(
    request: SoftwareRequest,
    service: SoftwareService = Depends(get_software_service),
) -> SoftwareInstallResponse:
    try:
        return await service.request_uninstall(request.software_id)
    except SoftwareCatalogError as exc:
        raise _catalog_error(exc) from exc
