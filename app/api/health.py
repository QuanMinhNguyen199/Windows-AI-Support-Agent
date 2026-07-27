from fastapi import APIRouter

from app.config import get_settings
from app.models.health import HealthResponse, ServiceStatus


router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        ollama=ServiceStatus(
            status="not_checked",
            detail="Kiểm tra Ollama sẽ được triển khai ở Giai đoạn 5.",
        ),
    )
