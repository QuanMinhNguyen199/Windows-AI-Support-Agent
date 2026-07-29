from app.core.command_registry import CommandRegistry
from app.database.repositories import PendingActionRepository
from app.models.actions import ActionKind
from app.models.repairs import RepairRequestResponse, RepairSummary


_REPAIRS = {
    "flush-dns": RepairSummary(
        id="flush-dns",
        display_name="Xóa DNS cache",
        description="Xóa bộ nhớ đệm phân giải tên miền của Windows.",
        warning="Các tên miền sẽ được phân giải lại. Kết nối hiện tại không bị xóa.",
    ),
    "release-ip": RepairSummary(
        id="release-ip",
        display_name="Giải phóng địa chỉ IP",
        description="Giải phóng địa chỉ do DHCP cấp cho các adapter.",
        warning="Máy có thể mất mạng cho đến khi địa chỉ IP được cấp lại.",
    ),
    "renew-ip": RepairSummary(
        id="renew-ip",
        display_name="Cấp lại địa chỉ IP",
        description="Yêu cầu DHCP cấp lại địa chỉ IP cho các adapter.",
        warning="Kết nối mạng có thể gián đoạn trong thời gian ngắn.",
    ),
}

_COMMAND_IDS = {
    "flush-dns": "repair.flush_dns",
    "release-ip": "repair.release_ip",
    "renew-ip": "repair.renew_ip",
}


class RepairService:
    def __init__(
        self, repository: PendingActionRepository, registry: CommandRegistry
    ) -> None:
        self.repository = repository
        self.registry = registry

    def list_repairs(self) -> list[RepairSummary]:
        return list(_REPAIRS.values())

    def request(self, repair_id: str) -> RepairRequestResponse:
        normalized = repair_id.strip().casefold()
        try:
            repair = _REPAIRS[normalized]
            definition = self.registry.get(_COMMAND_IDS[normalized])
        except KeyError as exc:
            raise ValueError("Tác vụ sửa chữa không nằm trong danh sách an toàn.") from exc
        record = self.repository.create(
            resource_id=normalized,
            kind=ActionKind.NETWORK_REPAIR,
            definition=definition,
            warning=repair.warning,
        )
        return RepairRequestResponse(
            repair=repair,
            pending_action=self.repository.public(record),
            message="Đã chuẩn bị tác vụ; command chưa chạy cho đến khi bạn xác nhận.",
        )
