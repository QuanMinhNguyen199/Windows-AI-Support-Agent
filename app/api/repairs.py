from fastapi import APIRouter, Depends, HTTPException

from app.api.software import get_software_service
from app.models.repairs import RepairRequestResponse, RepairSummary
from app.services.repair_service import RepairService
from app.services.software_service import SoftwareService


router = APIRouter(prefix="/api/repairs", tags=["repairs"])


def get_repair_service(
    software: SoftwareService = Depends(get_software_service),
) -> RepairService:
    return RepairService(software.repository, software.registry)


@router.get("", response_model=list[RepairSummary])
def list_repairs(
    service: RepairService = Depends(get_repair_service),
) -> list[RepairSummary]:
    return service.list_repairs()


@router.post("/{repair_id}", response_model=RepairRequestResponse)
def request_repair(
    repair_id: str,
    service: RepairService = Depends(get_repair_service),
) -> RepairRequestResponse:
    try:
        return service.request(repair_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
