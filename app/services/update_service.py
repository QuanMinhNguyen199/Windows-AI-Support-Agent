import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models.patches import UpdateStatus

GITHUB_LATEST_RELEASE = (
    "https://api.github.com/repos/QuanMinhNguyen199/"
    "Windows-AI-Support-Agent/releases/latest"
)


def _version_tuple(value: str) -> tuple[int, int, int]:
    normalized = value.strip().removeprefix("v")
    parts = normalized.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError("Phiên bản GitHub không hợp lệ.")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


class UpdateService:
    def __init__(self, current_version: str, release_url: str = GITHUB_LATEST_RELEASE):
        self.current_version = current_version
        self.release_api_url = release_url

    def check(self) -> UpdateStatus:
        request = Request(
            self.release_api_url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "WinAssist"},
        )
        try:
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                return UpdateStatus(
                    current_version=self.current_version,
                    message="Chưa có bản phát hành chính thức trên GitHub.",
                )
            return self._unavailable()
        except (URLError, OSError, TimeoutError, json.JSONDecodeError):
            return self._unavailable()

        latest = str(payload.get("tag_name") or "").removeprefix("v")
        try:
            update_available = _version_tuple(latest) > _version_tuple(
                self.current_version
            )
        except ValueError:
            return self._unavailable("Thông tin phiên bản trên GitHub không hợp lệ.")
        assets = payload.get("assets") or []
        installer = next(
            (
                asset
                for asset in assets
                if str(asset.get("name", "")).lower().endswith("-setup.exe")
            ),
            None,
        )
        installer_url = installer.get("browser_download_url") if installer else None
        if not update_available:
            message = "Bạn đang dùng phiên bản mới nhất."
        elif installer_url:
            message = "Có bản mới. Bạn có thể tải và cập nhật ngay trong ứng dụng."
        else:
            message = "Có bản mới nhưng installer Windows chưa được phát hành."
        return UpdateStatus(
            current_version=self.current_version,
            latest_version=latest,
            update_available=update_available,
            installer_available=bool(installer_url),
            installer_url=installer_url,
            release_url=payload.get("html_url"),
            message=message,
        )

    def _unavailable(self, message: str = "Không thể kiểm tra cập nhật lúc này.") -> UpdateStatus:
        return UpdateStatus(current_version=self.current_version, message=message)
