from typing import Literal

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    status: Literal["available", "unavailable", "not_checked"]
    detail: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    application: str
    version: str
    ollama: ServiceStatus
