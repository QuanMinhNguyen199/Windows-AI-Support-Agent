import io
import json
from unittest.mock import patch
from urllib.error import HTTPError

from app.services.update_service import UpdateService


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.body = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self) -> bytes:
        return self.body.read()


def test_update_service_finds_new_windows_installer() -> None:
    payload = {
        "tag_name": "v1.0.0",
        "html_url": "https://github.com/example/releases/tag/v1.0.0",
        "assets": [
            {
                "name": "WinAssist-1.0.0-Setup.exe",
                "browser_download_url": "https://github.com/example/setup.exe",
                "digest": "sha256:" + "a" * 64,
            }
        ],
    }
    with patch("app.services.update_service.urlopen", return_value=FakeResponse(payload)):
        status = UpdateService("0.9.7").check()

    assert status.update_available is True
    assert status.installer_available is True
    assert status.latest_version == "1.0.0"
    assert status.installer_url == "https://github.com/example/setup.exe"
    assert status.installer_sha256 == "a" * 64


def test_update_service_explains_missing_release() -> None:
    error = HTTPError("https://example.test", 404, "Not Found", {}, None)
    with patch("app.services.update_service.urlopen", side_effect=error):
        status = UpdateService("0.9.7").check()

    assert status.update_available is False
    assert status.latest_version is None
    assert "Chưa có bản phát hành" in status.message
