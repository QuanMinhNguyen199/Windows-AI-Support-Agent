import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/debug", tags=["debug"])
logger = logging.getLogger("winassist")


class ClientErrorReport(BaseModel):
    error_type: str = Field(default="JavaScriptError", max_length=80)
    message: str = Field(max_length=500)
    source: str | None = Field(default=None, max_length=200)
    line: int | None = Field(default=None, ge=0)


@router.post("/client-error", status_code=204)
def report_client_error(report: ClientErrorReport) -> None:
    logger.error(
        "client_error",
        extra={
            "exception_type": report.error_type,
            "error_detail": report.message,
            "source": report.source,
            "line": report.line,
        },
    )
