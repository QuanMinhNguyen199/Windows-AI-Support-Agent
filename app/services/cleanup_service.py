import asyncio
import json

from app.core.command_registry import CommandRegistry
from app.core.command_runner import CommandRunner
from app.database.repositories import PendingActionRepository
from app.models.actions import ActionKind
from app.models.cleanup import (
    CleanupCategory,
    CleanupRequestResponse,
    CleanupScanResponse,
)


_CATEGORIES = {
    "user_temp": (
        "File tạm của ứng dụng",
        "File cũ trong thư mục tạm; file đang dùng sẽ được bỏ qua.",
    ),
    "thumbnail_cache": (
        "Ảnh xem trước",
        "Bộ nhớ ảnh thu nhỏ; Windows sẽ tự tạo lại khi cần.",
    ),
    "crash_dumps": (
        "Báo cáo ứng dụng bị lỗi",
        "File ghi lại lỗi cũ của ứng dụng, không phải tài liệu cá nhân.",
    ),
}


class CleanupService:
    def __init__(
        self,
        repository: PendingActionRepository,
        registry: CommandRegistry,
        runner: CommandRunner,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.runner = runner

    async def scan(self) -> CleanupScanResponse:
        ids = tuple(_CATEGORIES)
        results = await asyncio.gather(
            *(self.runner.run(self.registry.cleanup_scan(item)) for item in ids)
        )
        categories: list[CleanupCategory] = []
        for category_id, result in zip(ids, results, strict=True):
            if not result.success:
                raise RuntimeError(
                    "Windows không đọc được file tạm. Hãy thử quét lại hoặc mở lại WinAssist."
                )
            payload: dict[str, object] = {}
            try:
                parsed = json.loads(result.stdout)
                if not isinstance(parsed, dict):
                    raise ValueError("Kết quả quét không đúng định dạng.")
                payload = parsed
            except (json.JSONDecodeError, ValueError) as exc:
                raise RuntimeError(
                    "Windows trả về kết quả quét không hợp lệ. Hãy thử lại."
                ) from exc
            title, description = _CATEGORIES[category_id]
            categories.append(
                CleanupCategory(
                    id=category_id,
                    title=title,
                    description=description,
                    file_count=int(payload.get("file_count") or 0),
                    bytes=int(payload.get("bytes") or 0),
                )
            )
        total = sum(item.bytes for item in categories)
        return CleanupScanResponse(
            categories=categories,
            total_bytes=total,
            message=(
                "Đã quét xong. Hãy tự chọn mục muốn dọn."
                if total
                else "Máy hiện không có file tạm đáng kể trong các nhóm an toàn."
            ),
        )

    def request(self, categories: list[str]) -> CleanupRequestResponse:
        normalized = tuple(sorted(set(item.strip().casefold() for item in categories)))
        if not normalized or any(item not in _CATEGORIES for item in normalized):
            raise ValueError("Nhóm file tạm không nằm trong danh sách an toàn.")
        definition = self.registry.cleanup_selected(normalized)
        record = self.repository.create(
            resource_id="cleanup:" + ",".join(normalized),
            kind=ActionKind.SYSTEM_CLEANUP,
            definition=definition,
            warning=(
                "WinAssist chỉ xóa các nhóm bạn đã chọn. Downloads, Documents, "
                "Desktop, Thùng rác và file đang sử dụng không bị xóa."
            ),
        )
        return CleanupRequestResponse(
            pending_action=self.repository.public(record),
            message="Đã chuẩn bị dọn dẹp; chưa xóa file trước khi bạn xác nhận.",
        )
