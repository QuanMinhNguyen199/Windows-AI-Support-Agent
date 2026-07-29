from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.diagnostics import (
    NetworkDiagnosticResponse,
    PingDiagnosticResponse,
    PingTarget,
    SpeedTestResponse,
)
from app.services.network_service import NetworkService
from app.services.speedtest_service import OoklaSpeedTestProvider


router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


class PingRequest(BaseModel):
    target: PingTarget


@lru_cache
def get_network_service() -> NetworkService:
    return NetworkService()


@lru_cache
def get_speedtest_provider() -> OoklaSpeedTestProvider:
    return OoklaSpeedTestProvider()


@router.post("/network", response_model=NetworkDiagnosticResponse)
async def diagnose_network(
    service: NetworkService = Depends(get_network_service),
) -> NetworkDiagnosticResponse:
    return await service.run_diagnostic()


@router.post("/ping", response_model=PingDiagnosticResponse)
async def diagnose_ping(
    request: PingRequest,
    service: NetworkService = Depends(get_network_service),
) -> PingDiagnosticResponse:
    return await service.run_ping(request.target)


@router.post("/speedtest", response_model=SpeedTestResponse)
async def diagnose_speed(
    provider: OoklaSpeedTestProvider = Depends(get_speedtest_provider),
) -> SpeedTestResponse:
    return await provider.run_test()
