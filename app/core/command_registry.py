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
    risk_level: RiskLevel = RiskLevel.READ_ONLY,
) -> CommandDefinition:
    return CommandDefinition(
        id=command_id,
        executable=executable,
        arguments=arguments,
        risk_level=risk_level,
        requires_admin=False,
        timeout_seconds=timeout_seconds,
        description=description,
    )


_COMMANDS = {
    "windows.battery": _definition(
        "windows.battery",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$items=@(Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue|"
                "Select-Object Name,BatteryStatus,EstimatedChargeRemaining,"
                "EstimatedRunTime);[pscustomobject]@{supported=($items.Count -gt 0);"
                "batteries=$items}|ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc trạng thái pin, không thay đổi power plan.",
    ),
    "windows.storage": _definition(
        "windows.storage",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$items=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3'|"
                "Select-Object DeviceID,VolumeName,Size,FreeSpace);"
                "[pscustomobject]@{supported=$true;drives=$items}|"
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc dung lượng các ổ đĩa cục bộ.",
    ),
    "windows.devices": _definition(
        "windows.devices",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$cmd=Get-Command Get-PnpDevice -ErrorAction SilentlyContinue;"
                "$result=if($cmd){$items=@(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue|"
                "Where-Object {$_.Class -in @('AudioEndpoint','Media','Camera','Image',"
                "'Bluetooth')}|Select-Object Class,FriendlyName,Status,Problem);"
                "[pscustomobject]@{supported=$true;devices=$items}}else{"
                "[pscustomobject]@{supported=$false;devices=@()}};$result|"
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc trạng thái audio, camera, microphone và Bluetooth.",
        timeout_seconds=40,
    ),
    "windows.printers": _definition(
        "windows.printers",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$cmd=Get-Command Get-Printer -ErrorAction SilentlyContinue;"
                "$result=if($cmd){$items=@(Get-Printer -ErrorAction SilentlyContinue|"
                "ForEach-Object {$p=$_;$count=@(Get-PrintJob -PrinterName $p.Name "
                "-ErrorAction SilentlyContinue).Count;[pscustomobject]@{Name=$p.Name;"
                "DriverName=$p.DriverName;PortName=$p.PortName;PrinterStatus="
                "$p.PrinterStatus;JobCount=$count}});[pscustomobject]@{supported=$true;"
                "printers=$items}}else{[pscustomobject]@{supported=$false;printers=@()}};"
                "$result|"
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc máy in và số lượng print job, không đọc tên tài liệu.",
        timeout_seconds=40,
    ),
    "windows.update_status": _definition(
        "windows.update_status",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$svc=Get-Service wuauserv -ErrorAction SilentlyContinue;"
                "$hotfix=Get-HotFix -ErrorAction SilentlyContinue|"
                "Sort-Object InstalledOn -Descending|Select-Object -First 1 "
                "HotFixID,InstalledOn,Description;"
                "$pending=(Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\"
                "CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired');"
                "$status=if($svc){$svc.Status.ToString()}else{$null};"
                "$start=if($svc){$svc.StartType.ToString()}else{$null};"
                "[pscustomobject]@{supported=($null-ne $svc);service_status=$status;"
                "start_type=$start;"
                "reboot_pending=$pending;latest_hotfix=$hotfix}|"
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc trạng thái dịch vụ Windows Update và bản vá gần nhất.",
        timeout_seconds=40,
    ),
    "windows.datetime": _definition(
        "windows.datetime",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$tz=Get-TimeZone;[pscustomobject]@{supported=$true;"
                "local_time=(Get-Date).ToString('o');timezone_id=$tz.Id;"
                "timezone_name=$tz.DisplayName;utc_offset=(Get-Date).ToString('zzz')}|"
                "ConvertTo-Json -Compress"
            ),
        ),
        "Đọc ngày giờ và múi giờ hiện tại.",
    ),
    "windows.startup_apps": _definition(
        "windows.startup_apps",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$items=@(Get-CimInstance Win32_StartupCommand -ErrorAction "
                "SilentlyContinue|Select-Object Name,Location);"
                "[pscustomobject]@{supported=$true;apps=$items}|"
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        ),
        "Đọc tên ứng dụng startup, không đọc command hoặc user.",
        timeout_seconds=30,
    ),
    "software.inventory.winget_list": _definition(
        "software.inventory.winget_list",
        "winget",
        ("list", "--disable-interactivity"),
        "Đọc một lần danh sách package do winget nhận diện.",
        timeout_seconds=60,
    ),
    "system.get_specs": _definition(
        "system.get_specs",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$os=Get-CimInstance Win32_OperatingSystem;"
                "$cs=Get-CimInstance Win32_ComputerSystem;"
                "$cpu=Get-CimInstance Win32_Processor|Select-Object -First 1;"
                "$gpu=@(Get-CimInstance Win32_VideoController|Select-Object -ExpandProperty Name);"
                "$disk=Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='$($env:SystemDrive)'\";"
                "[pscustomobject]@{"
                "device_name=$env:COMPUTERNAME;"
                "manufacturer=$cs.Manufacturer;model=$cs.Model;"
                "os_name=$os.Caption;os_version=$os.Version;os_build=$os.BuildNumber;"
                "architecture=$os.OSArchitecture;"
                "cpu_name=$cpu.Name;physical_cores=$cpu.NumberOfCores;"
                "logical_processors=$cpu.NumberOfLogicalProcessors;"
                "memory_bytes=[int64]$cs.TotalPhysicalMemory;"
                "gpu_names=$gpu;system_drive=$disk.DeviceID;"
                "disk_size_bytes=[int64]$disk.Size;"
                "disk_free_bytes=[int64]$disk.FreeSpace"
                "}|ConvertTo-Json -Depth 3 -Compress"
            ),
        ),
        "Đọc thông số phần cứng và Windows cơ bản.",
        timeout_seconds=30,
    ),
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
    "network.speedtest": _definition(
        "network.speedtest",
        "powershell",
        (
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "$packages=Join-Path $env:LOCALAPPDATA 'Microsoft\\WinGet\\Packages';"
                "$package=Get-ChildItem -LiteralPath $packages -Directory "
                "-Filter 'Ookla.Speedtest.CLI_*'|Select-Object -First 1;"
                "$speedtest=if($package){Join-Path $package.FullName 'speedtest.exe'};"
                "if(!(Test-Path -LiteralPath $speedtest)){"
                "throw 'Ookla Speedtest CLI is not installed via winget.'};"
                "& $speedtest --accept-license --accept-gdpr "
                "--format=json --progress=no"
            ),
        ),
        "Đo tốc độ mạng bằng Ookla Speedtest CLI.",
        timeout_seconds=120,
    ),
    "repair.flush_dns": _definition(
        "repair.flush_dns",
        "ipconfig",
        ("/flushdns",),
        "Xóa DNS resolver cache của Windows.",
        risk_level=RiskLevel.LOW_RISK,
    ),
    "repair.release_ip": _definition(
        "repair.release_ip",
        "ipconfig",
        ("/release",),
        "Giải phóng địa chỉ IP DHCP hiện tại.",
        risk_level=RiskLevel.LOW_RISK,
    ),
    "repair.renew_ip": _definition(
        "repair.renew_ip",
        "ipconfig",
        ("/renew",),
        "Yêu cầu cấp lại địa chỉ IP từ DHCP.",
        timeout_seconds=60,
        risk_level=RiskLevel.LOW_RISK,
    ),
}


class CommandRegistry:
    ALLOWED_EXECUTABLES = frozenset(
        {
            "ipconfig",
            "ping",
            "nslookup",
            "netsh",
            "powershell",
            "where",
            "winget",
            "git",
            "python",
            "py",
            "node",
            "npm",
            "ollama",
            "speedtest",
            "taskkill",
        }
    )

    def __init__(
        self,
        software_commands: Mapping[str, tuple[tuple[str, ...], ...]] | None = None,
        software_packages: Mapping[str, str] | None = None,
        software_verification_commands: Mapping[
            str, tuple[tuple[str, ...], ...]
        ] | None = None,
        software_uninstall_commands: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        commands = dict(_COMMANDS)
        self._software_check_ids: dict[str, tuple[str, ...]] = {}
        self._software_install_ids: dict[str, str] = {}
        self._software_uninstall_ids: dict[str, str] = {}
        self._software_verification_ids: dict[str, tuple[str, ...]] = {}
        packages = software_packages or {}
        checks = software_commands or {}
        verification_commands = software_verification_commands or {}
        uninstall_commands = software_uninstall_commands or {}
        if set(packages) != set(checks):
            raise CommandRegistryError("Software package và check command không đồng bộ.")
        if not set(verification_commands).issubset(packages):
            raise CommandRegistryError("Software verification không thuộc catalog.")
        if not set(uninstall_commands).issubset(packages):
            raise CommandRegistryError("Software uninstall override không thuộc catalog.")
        for software_id, package_id in packages.items():
            check_ids: list[str] = []
            for index, command in enumerate(checks[software_id]):
                if not command:
                    raise CommandRegistryError("Software check command bị rỗng.")
                executable, *arguments = command
                if executable.casefold() not in self.ALLOWED_EXECUTABLES:
                    raise CommandRegistryError(
                        f"Executable catalog không được phép: {executable}"
                    )
                command_id = f"software.check.{software_id}.{index}"
                commands[command_id] = _definition(
                    command_id,
                    executable,
                    tuple(arguments),
                    f"Kiểm tra trạng thái cài đặt của {software_id}.",
                )
                check_ids.append(command_id)
            install_id = f"software.install.{software_id}"
            commands[install_id] = _definition(
                install_id,
                "winget",
                ("install", "--id", package_id, "--exact", "--disable-interactivity"),
                f"Cài package {package_id} từ winget.",
                timeout_seconds=120,
                risk_level=RiskLevel.LOW_RISK,
            )
            self._software_check_ids[software_id] = tuple(check_ids)
            verification_ids: list[str] = []
            for index, command in enumerate(
                verification_commands.get(software_id, ())
            ):
                executable, *arguments = command
                if executable.casefold() not in self.ALLOWED_EXECUTABLES:
                    raise CommandRegistryError(
                        f"Executable verification không được phép: {executable}"
                    )
                verification_id = f"software.verify.{software_id}.{index}"
                commands[verification_id] = _definition(
                    verification_id,
                    executable,
                    tuple(arguments),
                    f"Xác minh executable thực tế của {software_id}.",
                )
                verification_ids.append(verification_id)
            self._software_verification_ids[software_id] = tuple(verification_ids)
            self._software_install_ids[software_id] = install_id
            uninstall_id = f"software.uninstall.{software_id}"
            uninstall_command = uninstall_commands.get(software_id)
            uninstall_executable = "winget"
            uninstall_arguments = (
                "uninstall",
                "--id",
                package_id,
                "--exact",
                "--disable-interactivity",
            )
            if uninstall_command is not None:
                uninstall_executable, *custom_arguments = uninstall_command
                if uninstall_executable.casefold() not in self.ALLOWED_EXECUTABLES:
                    raise CommandRegistryError(
                        f"Executable uninstall không được phép: {uninstall_executable}"
                    )
                uninstall_arguments = tuple(custom_arguments)
            commands[uninstall_id] = _definition(
                uninstall_id,
                uninstall_executable,
                uninstall_arguments,
                f"Gỡ package {package_id} bằng winget.",
                timeout_seconds=120,
                risk_level=RiskLevel.LOW_RISK,
            )
            self._software_uninstall_ids[software_id] = uninstall_id
        self._commands: Mapping[str, CommandDefinition] = MappingProxyType(commands)

    def list(self) -> tuple[CommandDefinition, ...]:
        return tuple(self._commands.values())

    def get(self, command_id: str) -> CommandDefinition:
        try:
            return self._commands[command_id]
        except KeyError as exc:
            raise CommandRegistryError(f"Command ID không được phép: {command_id}") from exc

    def software_checks(self, software_id: str) -> tuple[CommandDefinition, ...]:
        try:
            return tuple(self.get(item) for item in self._software_check_ids[software_id])
        except KeyError as exc:
            raise CommandRegistryError(
                f"Software ID không được đăng ký: {software_id}"
            ) from exc

    def software_install(self, software_id: str) -> CommandDefinition:
        try:
            return self.get(self._software_install_ids[software_id])
        except KeyError as exc:
            raise CommandRegistryError(
                f"Software ID không được đăng ký: {software_id}"
            ) from exc

    def software_verifications(
        self, software_id: str
    ) -> tuple[CommandDefinition, ...]:
        try:
            return tuple(
                self.get(item) for item in self._software_verification_ids[software_id]
            )
        except KeyError as exc:
            raise CommandRegistryError(
                f"Software ID không được đăng ký: {software_id}"
            ) from exc

    def software_uninstall(self, software_id: str) -> CommandDefinition:
        try:
            return self.get(self._software_uninstall_ids[software_id])
        except KeyError as exc:
            raise CommandRegistryError(
                f"Software ID không được đăng ký: {software_id}"
            ) from exc

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

    def cancel_process_tree(self, process_id: int) -> CommandDefinition:
        if not isinstance(process_id, int) or process_id <= 0:
            raise CommandRegistryError("Process ID không hợp lệ.")
        return _definition(
            "process.cancel_tree",
            "taskkill",
            ("/PID", str(process_id), "/T", "/F"),
            "Dừng cây tiến trình installer theo yêu cầu người dùng.",
            risk_level=RiskLevel.LOW_RISK,
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
        if definition.id == "process.cancel_tree":
            if len(definition.arguments) != 4:
                raise CommandRegistryError("Lệnh dừng process thiếu tham số.")
            try:
                process_id = int(definition.arguments[1])
            except ValueError as exc:
                raise CommandRegistryError("Process ID không hợp lệ.") from exc
            if definition != self.cancel_process_tree(process_id):
                raise CommandRegistryError("Lệnh dừng process đã bị thay đổi.")
            return
        raise CommandRegistryError(
            f"Command definition không thuộc registry: {definition.id}"
        )
