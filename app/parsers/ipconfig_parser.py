import re
from ipaddress import IPv4Address, ip_address

from app.models.diagnostics import IPConfiguration


_ADAPTER_HEADER = re.compile(
    r"^\s*(.+?(?:\badapter\b|bộ điều hợp).+?):\s*$", re.IGNORECASE
)
_IPV4 = re.compile(r"(?<![0-9.])(?:\d{1,3}\.){3}\d{1,3}(?![0-9.])")
_PROPERTY = re.compile(r"^\s*([^:]+?)\s*:\s*(.*)$")


def _valid_ipv4_values(value: str) -> list[str]:
    found: list[str] = []
    for candidate in _IPV4.findall(value):
        try:
            parsed = ip_address(candidate)
        except ValueError:
            continue
        if isinstance(parsed, IPv4Address):
            found.append(str(parsed))
    return found


def parse_ipconfig(output: str) -> IPConfiguration:
    ipv4_addresses: list[str] = []
    gateways: list[str] = []
    dns_servers: list[str] = []
    connected: list[str] = []
    disconnected: list[str] = []
    current_adapter: str | None = None
    current_property = ""

    for line in output.splitlines():
        header = _ADAPTER_HEADER.match(line)
        if header:
            current_adapter = header.group(1).strip()
            current_property = ""
            continue

        prop = _PROPERTY.match(line)
        if prop:
            current_property = prop.group(1).casefold()
            value = prop.group(2).strip()
        elif line.startswith((" ", "\t")):
            value = line.strip()
        else:
            current_property = ""
            continue

        if "media state" in current_property or "trạng thái phương tiện" in current_property:
            if current_adapter and (
                "disconnected" in value.casefold() or "ngắt kết nối" in value.casefold()
            ):
                if current_adapter not in disconnected:
                    disconnected.append(current_adapter)
            continue

        values = _valid_ipv4_values(value)
        if "ipv4" in current_property:
            ipv4_addresses.extend(values)
            if current_adapter and values and current_adapter not in connected:
                connected.append(current_adapter)
        elif "default gateway" in current_property or "cổng mặc định" in current_property:
            gateways.extend(values)
        elif "dns servers" in current_property or "máy chủ dns" in current_property:
            dns_servers.extend(values)

    ipv4_addresses = list(dict.fromkeys(ipv4_addresses))
    gateways = list(dict.fromkeys(gateways))
    dns_servers = list(dict.fromkeys(dns_servers))
    return IPConfiguration(
        ipv4_addresses=ipv4_addresses,
        default_gateways=gateways,
        dns_servers=dns_servers,
        connected_adapters=connected,
        disconnected_adapters=disconnected,
        has_apipa=any(value.startswith("169.254.") for value in ipv4_addresses),
    )
