import os
import socket
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.desktop import (
    DESKTOP_HOST,
    DesktopController,
    SingleInstance,
    active_monitor_work_area,
    centered_window_geometry,
    configure_runtime_paths,
    desktop_icon_path,
    loopback_port_is_available,
)
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
        root / "data" / "logs" / "winassist.jsonl"
    )


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
