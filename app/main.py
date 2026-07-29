from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.actions import action_task_manager, router as actions_router
from app.api.chat import router as chat_router
from app.api.diagnostics import router as diagnostics_router
from app.api.health import router as health_router
from app.api.repairs import router as repairs_router
from app.api.software import router as software_router
from app.api.system import router as system_router
from app.config import BASE_DIR, get_settings
from app.database.db import Database


STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    from app.database.repositories import PendingActionRepository

    PendingActionRepository(database).recover_interrupted()
    yield
    await action_task_manager.shutdown()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trợ lý cài đặt và chẩn đoán Windows chạy local.",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(diagnostics_router)
app.include_router(software_router)
app.include_router(actions_router)
app.include_router(repairs_router)
app.include_router(system_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
