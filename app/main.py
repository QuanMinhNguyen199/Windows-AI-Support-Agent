from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.diagnostics import router as diagnostics_router
from app.api.health import router as health_router
from app.config import BASE_DIR, get_settings


STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trợ lý cài đặt và chẩn đoán Windows chạy local.",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(diagnostics_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
