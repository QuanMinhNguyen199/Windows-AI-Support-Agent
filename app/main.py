import secrets
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.actions import action_task_manager
from app.api.actions import router as actions_router
from app.api.chat import router as chat_router
from app.api.cleanup import router as cleanup_router
from app.api.diagnostics import router as diagnostics_router
from app.api.debug import router as debug_router
from app.api.health import router as health_router
from app.api.patches import router as patches_router
from app.api.repairs import router as repairs_router
from app.api.software import router as software_router
from app.api.system import router as system_router
from app.api.windows import router as windows_router
from app.config import BASE_DIR, get_settings
from app.core.logging_config import configure_local_logging
from app.database.db import Database
from app.services.software_change_watcher import software_registry_watcher

STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    from app.database.repositories import PendingActionRepository

    PendingActionRepository(database).recover_interrupted()
    import asyncio

    software_registry_watcher.start(asyncio.get_running_loop())
    try:
        yield
    finally:
        software_registry_watcher.stop()
        await action_task_manager.shutdown()


settings = get_settings()
request_logger = configure_local_logging(settings.log_path)
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trợ lý cài đặt và chẩn đoán Windows chạy local.",
    lifespan=lifespan,
)


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    started = time.perf_counter()
    status_code = 500
    caught_error: Exception | None = None
    try:
        desktop_token = settings.desktop_api_token
        supplied_token = request.query_params.get("desktop_token", "")
        session_token = request.cookies.get("winassist_desktop_session", "")
        valid_session = bool(desktop_token) and secrets.compare_digest(
            session_token,
            desktop_token,
        )
        if (
            desktop_token
            and request.url.path == "/"
            and secrets.compare_digest(supplied_token, desktop_token)
        ):
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(
                "winassist_desktop_session",
                desktop_token,
                httponly=True,
                samesite="strict",
            )
        elif (
            desktop_token
            and not valid_session
            and (
                request.url.path == "/"
                or (
                    request.url.path.startswith("/api/")
                    and request.url.path not in {"/api/health", "/api/ready"}
                )
            )
        ):
            response = JSONResponse(
                status_code=403,
                content={"detail": "Desktop session không hợp lệ."},
            )
        else:
            response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        caught_error = exc
        raise
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000)
        if "response" in locals():
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=()"
            )
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self' "
                "https://winassist-support.minhquanpro65.workers.dev; "
                "frame-ancestors 'none'"
            )
            response.headers["X-Request-ID"] = request_id
            if request.url.path.startswith("/api/"):
                response.headers["Cache-Control"] = "no-store"
            elif request.url.path == "/":
                response.headers["Cache-Control"] = "no-cache"
        if status_code >= 400 or caught_error is not None:
            request_logger.error(
                "http_error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "exception_type": type(caught_error).__name__ if caught_error else None,
                },
            )
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(diagnostics_router)
app.include_router(debug_router)
app.include_router(software_router)
app.include_router(actions_router)
app.include_router(cleanup_router)
app.include_router(repairs_router)
app.include_router(system_router)
app.include_router(windows_router)
app.include_router(patches_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
