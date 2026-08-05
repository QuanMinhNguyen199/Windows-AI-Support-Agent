from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.actions import PendingAction


class Intent(StrEnum):
    GREETING = "greeting"
    SOFTWARE_RECOMMENDATION = "software_recommendation"
    SOFTWARE_INSTALLATION = "software_installation"
    SOFTWARE_CHECK = "software_check"
    INSTALLATION_TROUBLESHOOTING = "installation_troubleshooting"
    SOFTWARE_UPDATE = "software_update"
    NETWORK_STATUS = "network_status"
    INTERNET_CONNECTION_ISSUE = "internet_connection_issue"
    NETWORK_SPEED_TEST = "network_speed_test"
    SLOW_NETWORK_DIAGNOSIS = "slow_network_diagnosis"
    WIFI_DIAGNOSIS = "wifi_diagnosis"
    DNS_DIAGNOSIS = "dns_diagnosis"
    PACKET_LOSS_DIAGNOSIS = "packet_loss_diagnosis"
    SYSTEM_INFORMATION = "system_information"
    BATTERY_STATUS = "battery_status"
    STORAGE_STATUS = "storage_status"
    DEVICE_STATUS = "device_status"
    PRINTER_STATUS = "printer_status"
    WINDOWS_UPDATE_STATUS = "windows_update_status"
    DATETIME_STATUS = "datetime_status"
    STARTUP_APPS_STATUS = "startup_apps_status"
    PERFORMANCE_ISSUE = "performance_issue"
    HELP = "help"
    FALLBACK = "fallback"


class RouterSource(StrEnum):
    OLLAMA = "ollama"
    RULE_BASED = "rule_based"


class IntentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    confidence: float = Field(ge=0, le=1)
    software_id: str | None = Field(default=None, max_length=64)
    reason: str = Field(default="", max_length=300)


class IntentDecision(IntentClassification):
    source: RouterSource


class AIExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    recommendations: list[str] = Field(default_factory=list, max_length=6)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)


class ChatSuggestion(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    message: str | None = Field(default=None, min_length=1, max_length=300)
    view: str | None = Field(
        default=None,
        pattern=r"^(overview|chat|suggestions|diagnostics|graphics|windows-update|activity|patches|support)$",
    )


class ChatResponse(BaseModel):
    session_id: str
    intent: Intent
    message: str
    diagnostic_steps: list[str] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    suggestions: list[ChatSuggestion] = Field(default_factory=list, max_length=6)
    pending_action: PendingAction | None = None
    warning: str | None = None
    router_source: RouterSource


class OllamaHealth(BaseModel):
    available: bool
    model_available: bool
    model: str
    detail: str
