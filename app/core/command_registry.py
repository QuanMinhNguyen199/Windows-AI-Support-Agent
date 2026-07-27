from ipaddress import ip_address
from types import MappingProxyType
from typing import Mapping

from app.models.command import CommandDefinition, RiskLevel


class CommandRegistryError(ValueError):
    """Raised when a command ID or its parameters are not allowed."""


def _definition(
    command_id: str,
    executable: str,
    arguments: tuple[str, ...],
    description: str,
    timeout_seconds: int = 20,
) -> CommandDefinition:
    return CommandDefinition(
        id=command_id,
        executable=executable,
        arguments=arguments,
        risk_level=RiskLevel.READ_ONLY,
        requires_admin=False,
        timeout_seconds=timeout_seconds,
        description=description,
    )


_COMMANDS = {
    "network.ipconfig_basic": _definition(
        "network.ipconfig_basic", "ipconfig", (), "Đọc cấu hình IP cơ bản."
    ),
    "network.ipconfig_all": _definition(
        "network.ipconfig_all", "ipconfig", ("/all",), "Đọc cấu hình IP đầy đủ."
    ),
    "network.get_adapters": _definition(
        "network.get_adapters",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed | ConvertTo-Json -Compress",
        ),
        "Đọc trạng thái network adapter.",
    ),
    "network.get_ip_configuration": _definition(
        "network.get_ip_configuration",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetIPConfiguration | Select-Object InterfaceAlias,InterfaceIndex,IPv4Address,IPv4DefaultGateway,DNSServer | ConvertTo-Json -Depth 4 -Compress",
        ),
        "Đọc IP, gateway và DNS theo interface.",
    ),
    "network.ping_localhost": _definition(
        "network.ping_localhost",
        "ping",
        ("127.0.0.1", "-n", "10"),
        "Kiểm tra TCP/IP stack cục bộ.",
        25,
    ),
    "network.ping_public_dns": _definition(
        "network.ping_public_dns",
        "ping",
        ("1.1.1.1", "-n", "10"),
        "Kiểm tra kết nối Internet tới 1.1.1.1.",
        25,
    ),
    "network.ping_google_dns": _definition(
        "network.ping_google_dns",
        "ping",
        ("8.8.8.8", "-n", "10"),
        "Kiểm tra kết nối Internet tới 8.8.8.8.",
        25,
    ),
    "network.ping_google": _definition(
        "network.ping_google",
        "ping",
        ("google.com", "-n", "10"),
        "So sánh kết nối hostname với kết nối IP.",
        25,
    ),
    "network.nslookup_google": _definition(
        "network.nslookup_google",
        "nslookup",
        ("google.com",),
        "Kiểm tra phân giải DNS cho google.com.",
    ),
    "network.wifi_interfaces": _definition(
        "network.wifi_interfaces",
        "netsh",
        ("wlan", "show", "interfaces"),
        "Đọc trạng thái kết nối Wi-Fi.",
    ),
    "network.wifi_drivers": _definition(
        "network.wifi_drivers",
        "netsh",
        ("wlan", "show", "drivers"),
        "Đọc thông tin driver Wi-Fi.",
    ),
}


class CommandRegistry:
    ALLOWED_EXECUTABLES = frozenset(
        {"ipconfig", "ping", "nslookup", "netsh", "powershell"}
    )

    def __init__(self) -> None:
        self._commands: Mapping[str, CommandDefinition] = MappingProxyType(_COMMANDS)

    def list(self) -> tuple[CommandDefinition, ...]:
        return tuple(self._commands.values())

    def get(self, command_id: str) -> CommandDefinition:
        try:
            return self._commands[command_id]
        except KeyError as exc:
            raise CommandRegistryError(f"Command ID không được phép: {command_id}") from exc

    def ping_gateway(self, target: str) -> CommandDefinition:
        try:
            validated = ip_address(target)
        except ValueError as exc:
            raise CommandRegistryError("Default gateway không phải địa chỉ IP hợp lệ.") from exc
        if validated.is_unspecified or validated.is_multicast:
            raise CommandRegistryError("Default gateway không phải target ping hợp lệ.")
        return _definition(
            "network.ping_gateway",
            "ping",
            (str(validated), "-n", "10"),
            "Kiểm tra kết nối tới default gateway đã phát hiện.",
            25,
        )

    def assert_registered(self, definition: CommandDefinition) -> None:
        static_definition = self._commands.get(definition.id)
        if static_definition is not None:
            if definition != static_definition:
                raise CommandRegistryError(
                    f"Command definition không khớp registry: {definition.id}"
                )
            return
        if definition.id == "network.ping_gateway":
            if not definition.arguments:
                raise CommandRegistryError("Ping gateway thiếu target.")
            expected = self.ping_gateway(definition.arguments[0])
            if definition != expected:
                raise CommandRegistryError("Ping gateway đã bị thay đổi arguments.")
            return
        raise CommandRegistryError(
            f"Command definition không thuộc registry: {definition.id}"
        )
