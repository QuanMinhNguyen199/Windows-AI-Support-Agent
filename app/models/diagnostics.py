from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.command import CommandResult


class DiagnosticStatus(StrEnum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PingTarget(StrEnum):
    LOCALHOST = "127.0.0.1"
    DEFAULT_GATEWAY = "default_gateway"
    CLOUDFLARE = "1.1.1.1"
    GOOGLE_DNS = "8.8.8.8"
    GOOGLE = "google.com"


class PingStatistics(BaseModel):
    sent: int | None = None
    received: int | None = None
    lost: int | None = None
    loss_percent: float | None = Field(default=None, ge=0, le=100)
    minimum_ms: float | None = Field(default=None, ge=0)
    maximum_ms: float | None = Field(default=None, ge=0)
    average_ms: float | None = Field(default=None, ge=0)


class IPConfiguration(BaseModel):
    ipv4_addresses: list[str] = Field(default_factory=list)
    default_gateways: list[str] = Field(default_factory=list)
    dns_servers: list[str] = Field(default_factory=list)
    connected_adapters: list[str] = Field(default_factory=list)
    disconnected_adapters: list[str] = Field(default_factory=list)
    has_apipa: bool = False

    @property
    def default_gateway(self) -> str | None:
        return self.default_gateways[0] if self.default_gateways else None


class WifiInformation(BaseModel):
    state: str | None = None
    ssid: str | None = None
    signal_percent: int | None = Field(default=None, ge=0, le=100)
    radio_type: str | None = None
    receive_rate_mbps: float | None = None
    transmit_rate_mbps: float | None = None
    channel: int | None = None
    authentication: str | None = None
    driver: str | None = None


class NetworkAdapter(BaseModel):
    name: str
    description: str | None = None
    status: str | None = None
    link_speed: str | None = None

    @property
    def is_up(self) -> bool:
        return (self.status or "").casefold() in {"up", "connected", "2"}


class DiagnosticFinding(BaseModel):
    status: DiagnosticStatus
    title: str
    detail: str
    evidence_command_ids: list[str] = Field(default_factory=list)


class PingDiagnosticResponse(BaseModel):
    target: PingTarget
    resolved_target: str
    status: DiagnosticStatus
    summary: str
    statistics: PingStatistics
    result: CommandResult


class NetworkDiagnosticResponse(BaseModel):
    status: DiagnosticStatus
    summary: str
    likely_cause: str
    confidence: ConfidenceLevel
    adapters: list[NetworkAdapter]
    ip_configuration: IPConfiguration
    wifi: WifiInformation
    findings: list[DiagnosticFinding]
    recommendations: list[str]
    results: list[CommandResult]
