import os
import socket
import sys
import hashlib
import base64
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.desktop import (
    DESKTOP_HOST,
    DesktopController,
    DesktopUpdater,
    SingleInstance,
    active_monitor_work_area,
    centered_window_geometry,
    configure_runtime_paths,
    desktop_icon_path,
    delayed_update_command,
    loopback_port_is_available,
)
from app import desktop
from app.main import app, settings


def test_desktop_icon_is_available() -> None:
    assert desktop_icon_path().is_file()


def test_runtime_data_is_stored_under_local_app_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    root = configure_runtime_paths()

    assert root == tmp_path / "WinAssist Local"
    assert os.environ["WINASSIST_DATABASE_PATH"] == str(
        root / "data" / "winassist.db"
    )
    assert os.environ["WINASSIST_LOG_PATH"] == str(
        root / "data" / "logs" / "debug-errors.jsonl"
    )


def test_desktop_crash_log_contains_traceback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    error = ValueError("desktop startup failed")

    path = desktop.write_desktop_crash_log(error)
    content = path.read_text(encoding="utf-8")

    assert path == tmp_path / "WinAssist Local" / "data" / "logs" / "desktop-crash.log"
    assert "ValueError: desktop startup failed" in content


def test_embedded_backend_config_works_without_console(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    config = desktop.embedded_uvicorn_config(app, DESKTOP_HOST, 8765)

    assert config.log_config is None
    assert config.access_log is False


class FakeDownloadResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.offset = 0
        self.headers = {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self, size: int = -1) -> bytes:
        if self.offset >= len(self.body):
            return b""
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        chunk = self.body[self.offset:end]
        self.offset = end
        return chunk


def test_desktop_updater_downloads_and_verifies_official_release(tmp_path, monkeypatch) -> None:
    body = b"verified installer"
    expected = hashlib.sha256(body).hexdigest()
    updater = DesktopUpdater(runtime_root=tmp_path, available=True)
    monkeypatch.setattr(desktop, "urlopen", lambda *_args, **_kwargs: FakeDownloadResponse(body))

    started = updater.start(
        "https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/download/v1.0.0/WinAssist-1.0.0-Setup.exe",
        "1.0.0",
        expected,
    )
    updater._thread.join(timeout=2)  # type: ignore[union-attr]

    assert started["success"] is True
    assert updater.status()["state"] == "ready"
    assert updater.status()["percent"] == 100
    assert (tmp_path / "updates" / "WinAssist-1.0.0-Setup.exe").read_bytes() == body


def test_desktop_updater_resumes_pending_download_on_startup(tmp_path, monkeypatch) -> None:
    body = b"verified installer after restart"
    expected = hashlib.sha256(body).hexdigest()
    update_dir = tmp_path / "updates"
    update_dir.mkdir()
    installer = update_dir / "WinAssist-1.0.0-Setup.exe"
    installer.with_suffix(".exe.part").write_bytes(b"partial")
    (update_dir / "pending-update.json").write_text(
        json.dumps(
            {
                "url": "https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/download/v1.0.0/WinAssist-1.0.0-Setup.exe",
                "version": "1.0.0",
                "sha256": expected,
                "installer": str(installer),
            }
        ),
        encoding="utf-8",
    )
    updater = DesktopUpdater(runtime_root=tmp_path, available=True)
    monkeypatch.setattr(desktop, "urlopen", lambda *_args, **_kwargs: FakeDownloadResponse(body))

    updater.resume_pending()
    updater._thread.join(timeout=2)  # type: ignore[union-attr]

    assert updater.status()["state"] == "ready"
    assert installer.read_bytes() == body
    assert not (update_dir / "pending-update.json").exists()


def test_desktop_updater_rejects_untrusted_url(tmp_path) -> None:
    updater = DesktopUpdater(runtime_root=tmp_path, available=True)

    response = updater.start(
        "https://example.com/WinAssist-1.0.0-Setup.exe",
        "1.0.0",
        "a" * 64,
    )

    assert response["success"] is False
    assert updater.status()["state"] == "idle"


def test_desktop_updater_rejects_checksum_mismatch(tmp_path, monkeypatch) -> None:
    updater = DesktopUpdater(runtime_root=tmp_path, available=True)
    monkeypatch.setattr(desktop, "urlopen", lambda *_args, **_kwargs: FakeDownloadResponse(b"bad"))

    updater.start(
        "https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/download/v1.0.0/WinAssist-1.0.0-Setup.exe",
        "1.0.0",
        "a" * 64,
    )
    updater._thread.join(timeout=2)  # type: ignore[union-attr]

    assert updater.status()["state"] == "failed"
    assert not (tmp_path / "updates" / "WinAssist-1.0.0-Setup.exe").exists()


def test_desktop_controller_installs_verified_update_and_exits(tmp_path, monkeypatch) -> None:
    body = b"installer"
    expected = hashlib.sha256(body).hexdigest()
    updater = DesktopUpdater(runtime_root=tmp_path, available=True)
    monkeypatch.setattr(desktop, "urlopen", lambda *_args, **_kwargs: FakeDownloadResponse(body))
    updater.start(
        "https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/download/v1.0.0/WinAssist-1.0.0-Setup.exe",
        "1.0.0",
        expected,
    )
    updater._thread.join(timeout=2)  # type: ignore[union-attr]
    calls: list[list[str]] = []
    monkeypatch.setattr(
        desktop.subprocess,
        "Popen",
        lambda arguments, **_kwargs: calls.append(arguments) or object(),
    )
    window = FakeWindow()
    controller = DesktopController(updater=updater)
    controller.bind(window)

    response = controller.install_update()

    assert response["success"] is True
    update_script = base64.b64decode(calls[0][-1]).decode("utf-16-le")
    assert "/VERYSILENT" in update_script
    assert "/UPDATE=1" in update_script
    assert "/MERGETASKS=desktopicon" in update_script
    assert "Wait-Process" in update_script
    assert controller.exit_requested is True
    assert window.destroyed is True


def test_delayed_update_runs_hidden_without_setup_wizard(tmp_path) -> None:
    installer = tmp_path / "WinAssist-1.2.3-Setup.exe"

    command = delayed_update_command(installer, 1234)
    script = base64.b64decode(command[-1]).decode("utf-16-le")

    assert command[3:5] == ["-WindowStyle", "Hidden"]
    assert "Wait-Process -Id 1234" in script
    assert "/VERYSILENT" in script
    assert "/SP-" in script
    assert "/NORESTART" in script
    assert "/MERGETASKS=desktopicon" in script


def test_loopback_port_check_detects_collision() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((DESKTOP_HOST, 0))
        port = listener.getsockname()[1]

        assert loopback_port_is_available(port=port) is False

    assert loopback_port_is_available(port=port) is True


def test_window_is_centered_inside_work_area() -> None:
    x, y, width, height = centered_window_geometry((0, 0, 1536, 912))

    assert (x, y, width, height) == (128, 46, 1280, 820)
    assert y + height <= 912


def test_window_fits_small_and_offset_monitor() -> None:
    x, y, width, height = centered_window_geometry((-1280, 20, 0, 740))

    assert x >= -1280
    assert y >= 20
    assert x + width <= 0
    assert y + height <= 740


class FakeWindow:
    def __init__(self) -> None:
        self.hidden = False
        self.destroyed = False

    def hide(self) -> None:
        self.hidden = True

    def destroy(self) -> None:
        self.destroyed = True


class FakeDialogWindow(FakeWindow):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []

    def evaluate_js(self, script: str) -> bool:
        self.scripts.append(script)
        return True


def test_closing_opens_in_app_dialog_without_blocking_native_event(monkeypatch) -> None:
    window = FakeDialogWindow()
    controller = DesktopController()
    controller.bind(window)
    scheduled: list[object] = []

    class FakeTimer:
        def __init__(self, _delay, callback) -> None:
            scheduled.append(callback)

        def start(self) -> None:
            return None

    monkeypatch.setattr(desktop.threading, "Timer", FakeTimer)

    should_close = controller.on_closing()

    assert should_close is False
    assert window.destroyed is False
    assert window.scripts == []
    assert len(scheduled) == 1

    scheduled[0]()

    assert window.scripts == ["window.WinAssistDesktop?.showCloseDialog?.() ?? false"]
    assert controller._close_dialog_pending is False


def test_native_window_is_not_exposed_as_public_js_api_state() -> None:
    controller = DesktopController()
    controller.bind(FakeWindow())

    assert "window" not in vars(controller)
    assert vars(controller)["_window"] is not None


def test_desktop_controller_hides_to_tray_or_exits() -> None:
    window = FakeWindow()
    controller = DesktopController()
    controller.bind(window)
    controller.tray_available = True

    hidden = controller.close_to_tray()

    assert hidden["success"] is True
    assert window.hidden is True

    exited = controller.exit_app()

    assert exited["success"] is True
    assert controller.exit_requested is True
    assert window.destroyed is True


def test_desktop_controller_does_not_hide_without_tray() -> None:
    window = FakeWindow()
    controller = DesktopController()
    controller.bind(window)

    response = controller.close_to_tray()

    assert response["success"] is False
    assert window.hidden is False


def test_desktop_controller_uninstall_requires_installed_build(monkeypatch) -> None:
    controller = DesktopController()
    monkeypatch.setattr(desktop, "installed_uninstaller_path", lambda: None)

    assert controller.uninstall_status()["available"] is False
    assert controller.uninstall_app()["success"] is False
    assert controller.exit_requested is False


def test_desktop_controller_launches_trusted_uninstaller(tmp_path, monkeypatch) -> None:
    uninstaller = tmp_path / "unins000.exe"
    uninstaller.write_bytes(b"test")
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_popen(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return object()

    window = FakeWindow()
    controller = DesktopController()
    controller.bind(window)
    monkeypatch.setattr(desktop, "installed_uninstaller_path", lambda: uninstaller)
    monkeypatch.setattr(desktop.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(desktop.os, "getpid", lambda: 4242)

    response = controller.uninstall_app()

    assert response["success"] is True
    command = calls[0][0]
    assert command[0].endswith(r"WindowsPowerShell\v1.0\powershell.exe")
    encoded_script = command[command.index("-EncodedCommand") + 1]
    script = desktop.base64.b64decode(encoded_script).decode("utf-16-le")
    assert "Wait-Process -Id 4242" in script
    assert str(uninstaller) in script
    assert "'/PURGEDATA=1'" in script
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["creationflags"] == getattr(desktop.subprocess, "CREATE_NO_WINDOW", 0)
    assert controller.exit_requested is True
    assert window.destroyed is True


@pytest.mark.skipif(os.name != "nt", reason="Windows monitor API only")
def test_active_monitor_work_area_is_valid() -> None:
    left, top, right, bottom = active_monitor_work_area()

    assert right > left
    assert bottom > top


@pytest.mark.skipif(os.name != "nt", reason="Windows mutex only")
def test_single_instance_mutex_rejects_duplicate() -> None:
    name = rf"Local\WinAssistTest-{uuid4()}"
    first = SingleInstance(name)
    second = SingleInstance(name)
    try:
        assert first.acquire() is True
        assert second.acquire() is False
    finally:
        second.release()
        first.release()


def test_desktop_token_protects_local_api() -> None:
    previous = settings.desktop_api_token
    settings.desktop_api_token = "desktop-test-token"
    try:
        with TestClient(app) as client:
            denied = client.get("/api/patches/latest")
            health = client.get("/api/health")
            readiness = client.get("/api/ready")
            bootstrap = client.get(
                "/?desktop_token=desktop-test-token",
                follow_redirects=False,
            )
            allowed = client.get("/api/patches/latest")
    finally:
        settings.desktop_api_token = previous

    assert denied.status_code == 403
    assert health.status_code == 200
    assert readiness.status_code == 200
    assert bootstrap.status_code == 303
    assert bootstrap.headers["location"] == "/"
    assert allowed.status_code == 200
