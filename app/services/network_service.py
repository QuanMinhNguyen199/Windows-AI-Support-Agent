import asyncio
from typing import Protocol

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.models.command import CommandDefinition, CommandResult
from app.models.diagnostics import (
    ConfidenceLevel,
    DiagnosticFinding,
    DiagnosticStatus,
    NetworkAdapter,
    NetworkDiagnosticResponse,
    PingDiagnosticResponse,
    PingTarget,
)
from app.parsers.ipconfig_parser import parse_ipconfig
from app.parsers.net_adapter_parser import parse_net_adapters
from app.parsers.netsh_wlan_parser import parse_wlan_interfaces
from app.parsers.ping_parser import describe_ping, parse_ping


class Runner(Protocol):
    async def run(self, definition: CommandDefinition, *, confirmed: bool = False) -> CommandResult:
        ...


class NetworkService:
    def __init__(
        self,
        runner: Runner | None = None,
        registry: CommandRegistry | None = None,
    ) -> None:
        self.runner = runner or CommandRunner()
        self.registry = registry or CommandRegistry()

    async def run_diagnostic(self) -> NetworkDiagnosticResponse:
        initial_ids = (
            "network.get_adapters",
            "network.get_ip_configuration",
            "network.ipconfig_all",
        )
        initial = await asyncio.gather(
            *(self.runner.run(self.registry.get(command_id)) for command_id in initial_ids)
        )
        adapters = parse_net_adapters(initial[0].stdout)
        ip_configuration = parse_ipconfig(initial[2].stdout)

        definitions = [
            self.registry.get("network.ping_localhost"),
            self.registry.get("network.ping_public_dns"),
            self.registry.get("network.nslookup_google"),
            self.registry.get("network.ping_google"),
            self.registry.get("network.wifi_interfaces"),
            self.registry.get("network.wifi_drivers"),
        ]
        if ip_configuration.default_gateway:
            definitions.insert(1, self.registry.ping_gateway(ip_configuration.default_gateway))
        remaining = await asyncio.gather(*(self.runner.run(item) for item in definitions))
        results = [*initial, *remaining]
        by_id = {result.command_id: result for result in results}

        wifi = parse_wlan_interfaces(
            by_id["network.wifi_interfaces"].stdout,
            by_id["network.wifi_drivers"].stdout,
        )
        findings, recommendations, status, cause, confidence = self._analyze(
            ip_configuration, wifi.signal_percent, adapters, by_id
        )
        summary = findings[0].detail if findings else "Chưa đủ dữ liệu để kết luận."
        return NetworkDiagnosticResponse(
            status=status,
            summary=summary,
            likely_cause=cause,
            confidence=confidence,
            adapters=adapters,
            ip_configuration=ip_configuration,
            wifi=wifi,
            findings=findings,
            recommendations=recommendations,
            results=results,
        )

    async def run_ping(self, target: PingTarget) -> PingDiagnosticResponse:
        definition: CommandDefinition
        resolved_target = target.value
        if target is PingTarget.DEFAULT_GATEWAY:
            ipconfig = await self.runner.run(self.registry.get("network.ipconfig_all"))
            configuration = parse_ipconfig(ipconfig.stdout)
            if not configuration.default_gateway:
                return PingDiagnosticResponse(
                    target=target,
                    resolved_target="",
                    status=DiagnosticStatus.UNKNOWN,
                    summary="Không tìm thấy default gateway để kiểm tra.",
                    statistics=parse_ping(""),
                    result=ipconfig,
                )
            resolved_target = configuration.default_gateway
            definition = self.registry.ping_gateway(resolved_target)
        else:
            command_ids = {
                PingTarget.LOCALHOST: "network.ping_localhost",
                PingTarget.CLOUDFLARE: "network.ping_public_dns",
                PingTarget.GOOGLE_DNS: "network.ping_google_dns",
                PingTarget.GOOGLE: "network.ping_google",
            }
            definition = self.registry.get(command_ids[target])

        result = await self.runner.run(definition)
        statistics = parse_ping(result.stdout)
        status_value, summary = describe_ping(statistics)
        if not result.success and statistics.loss_percent is None:
            status_value = "error" if not result.timed_out else "warning"
            summary = "Lệnh ping không hoàn tất thành công."
        return PingDiagnosticResponse(
            target=target,
            resolved_target=resolved_target,
            status=DiagnosticStatus(status_value),
            summary=summary,
            statistics=statistics,
            result=result,
        )

    @staticmethod
    def _dns_succeeded(result: CommandResult) -> bool:
        lowered = f"{result.stdout}\n{result.stderr}".casefold()
        failure_markers = (
            "timed out",
            "timeout",
            "can't find",
            "non-existent domain",
            "server failed",
            "không tìm thấy",
            "hết thời gian",
        )
        return result.success and not any(marker in lowered for marker in failure_markers)

    def _analyze(
        self,
        config,
        wifi_signal: int | None,
        adapters: list[NetworkAdapter],
        results: dict[str, CommandResult],
    ) -> tuple[
        list[DiagnosticFinding],
        list[str],
        DiagnosticStatus,
        str,
        ConfidenceLevel,
    ]:
        findings: list[DiagnosticFinding] = []
        recommendations: list[str] = []
        localhost_ping = results["network.ping_localhost"]
        public_ping = results["network.ping_public_dns"]
        dns_ok = self._dns_succeeded(results["network.nslookup_google"])
        gateway_ping = results.get("network.ping_gateway")

        if adapters and not any(adapter.is_up for adapter in adapters):
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Không có network adapter hoạt động",
                    detail="Get-NetAdapter không ghi nhận adapter nào ở trạng thái Up.",
                    evidence_command_ids=["network.get_adapters"],
                )
            )
            recommendations.append("Kiểm tra Wi-Fi đã bật hoặc cáp Ethernet đã kết nối.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Adapter mạng đang tắt, mất kết nối hoặc chưa sẵn sàng.",
                ConfidenceLevel.HIGH,
            )

        if not localhost_ping.success:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="TCP/IP stack cục bộ không phản hồi",
                    detail="Ping 127.0.0.1 thất bại; chưa nên kết luận về router hoặc ISP.",
                    evidence_command_ids=["network.ping_localhost"],
                )
            )
            recommendations.append(
                "Khởi động lại máy; nếu vẫn lỗi, cần hỗ trợ kỹ thuật kiểm tra TCP/IP stack."
            )
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Có khả năng TCP/IP stack cục bộ đang gặp lỗi.",
                ConfidenceLevel.MEDIUM,
            )

        if not config.ipv4_addresses:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Không có IPv4 hợp lệ",
                    detail="Không tìm thấy adapter có địa chỉ IPv4 trong kết quả ipconfig.",
                    evidence_command_ids=["network.ipconfig_all"],
                )
            )
            recommendations.append("Kiểm tra Wi-Fi/Ethernet đã kết nối và DHCP trên router.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Adapter chưa kết nối hoặc máy chưa nhận được địa chỉ từ DHCP.",
                ConfidenceLevel.MEDIUM,
            )

        if config.has_apipa:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Phát hiện địa chỉ APIPA",
                    detail="Máy đang dùng địa chỉ 169.254.x.x, thường xảy ra khi DHCP không cấp được IP.",
                    evidence_command_ids=["network.ipconfig_all"],
                )
            )
            recommendations.append("Kiểm tra router/DHCP và thử kết nối lại Wi-Fi hoặc cáp mạng.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Có khả năng máy không nhận được địa chỉ IP từ DHCP.",
                ConfidenceLevel.HIGH,
            )

        if not config.default_gateway:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.WARNING,
                    title="Không tìm thấy default gateway",
                    detail="Có IPv4 nhưng không tìm thấy gateway; chưa thể kiểm tra đường ra router.",
                    evidence_command_ids=["network.ipconfig_all"],
                )
            )
            recommendations.append("Kiểm tra cấu hình IP/DHCP của adapter đang hoạt động.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.WARNING,
                "Cấu hình IP có thể thiếu default gateway.",
                ConfidenceLevel.MEDIUM,
            )

        if gateway_ping and not gateway_ping.success:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Không ping được gateway",
                    detail="Máy có IP nhưng không liên lạc được với router/default gateway.",
                    evidence_command_ids=["network.ping_gateway"],
                )
            )
            recommendations.append("Kiểm tra tín hiệu Wi-Fi, cáp mạng và trạng thái router.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Lỗi có khả năng nằm ở mạng nội bộ, Wi-Fi hoặc router.",
                ConfidenceLevel.HIGH,
            )

        if public_ping.success and not dns_ok:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Kết nối IP hoạt động nhưng DNS lỗi",
                    detail="Ping 1.1.1.1 thành công nhưng nslookup google.com thất bại.",
                    evidence_command_ids=[
                        "network.ping_public_dns",
                        "network.nslookup_google",
                    ],
                )
            )
            recommendations.append("Kiểm tra DNS đang cấu hình; có thể cân nhắc flush DNS sau khi xác nhận.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Có khả năng DNS đang lỗi hoặc không phản hồi.",
                ConfidenceLevel.HIGH,
            )

        if gateway_ping and gateway_ping.success and not public_ping.success:
            findings.append(
                DiagnosticFinding(
                    status=DiagnosticStatus.ERROR,
                    title="Mạng nội bộ hoạt động, Internet không phản hồi",
                    detail="Ping gateway thành công nhưng ping 1.1.1.1 thất bại.",
                    evidence_command_ids=[
                        "network.ping_gateway",
                        "network.ping_public_dns",
                    ],
                )
            )
            recommendations.append("Kiểm tra trạng thái WAN của router hoặc liên hệ ISP.")
            return (
                findings,
                recommendations,
                DiagnosticStatus.ERROR,
                "Có khả năng router mất kết nối WAN hoặc ISP đang gặp sự cố.",
                ConfidenceLevel.MEDIUM,
            )

        if public_ping.success and dns_ok:
            detail = "Gateway, kết nối IP Internet và phân giải DNS đều phản hồi."
            status = DiagnosticStatus.SUCCESS
            cause = "Chưa phát hiện lỗi kết nối mạng cơ bản."
            if wifi_signal is not None and wifi_signal < 40:
                status = DiagnosticStatus.WARNING
                detail += f" Tuy nhiên tín hiệu Wi-Fi chỉ {wifi_signal}% và đang yếu."
                cause = "Kết nối hoạt động nhưng tín hiệu Wi-Fi yếu có thể làm mạng không ổn định."
                recommendations.append("Di chuyển gần router hoặc giảm vật cản/nhiễu Wi-Fi.")
            elif wifi_signal is not None and wifi_signal <= 60:
                recommendations.append("Tín hiệu Wi-Fi ở mức trung bình; theo dõi packet loss khi sử dụng.")
            findings.append(
                DiagnosticFinding(
                    status=status,
                    title="Kiểm tra kết nối cơ bản hoàn tất",
                    detail=detail,
                    evidence_command_ids=[
                        "network.ping_gateway",
                        "network.ping_public_dns",
                        "network.nslookup_google",
                    ],
                )
            )
            recommendations.append(
                "Nếu ứng dụng vẫn lỗi, kiểm tra proxy, VPN, trình duyệt hoặc firewall của ứng dụng."
            )
            return findings, recommendations, status, cause, ConfidenceLevel.HIGH

        findings.append(
            DiagnosticFinding(
                status=DiagnosticStatus.UNKNOWN,
                title="Chưa đủ dữ liệu",
                detail="Một hoặc nhiều kiểm tra không trả về dữ liệu có thể phân tích.",
                evidence_command_ids=list(results),
            )
        )
        recommendations.append("Chạy lại kiểm tra và xem lỗi chi tiết của từng command.")
        return (
            findings,
            recommendations,
            DiagnosticStatus.UNKNOWN,
            "Chưa thể xác định nguyên nhân.",
            ConfidenceLevel.LOW,
        )
