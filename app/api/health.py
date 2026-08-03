from fastapi import APIRouter, Depends

from app.config import get_settings
from app.models.health import HealthResponse, ReadinessResponse, ServiceStatus
from app.services.ollama_service import OllamaService, get_ollama_service


router = APIRouter(tags=["health"])


@router.get("/api/ready", response_model=ReadinessResponse)
def readiness_check() -> ReadinessResponse:
    settings = get_settings()
    return ReadinessResponse(
        status="ready",
        application=settings.app_name,
        version=settings.app_version,
    )


@router.get("/api/health", response_model=HealthResponse)
async def health_check(
    ollama: OllamaService = Depends(get_ollama_service),
) -> HealthResponse:
    settings = get_settings()
    ollama_health = await ollama.health()
    ready = ollama_health.available and ollama_health.model_available
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        ollama=ServiceStatus(
            status="available" if ready else "unavailable",
            detail=ollama_health.detail,
        ),
    )
