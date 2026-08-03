from __future__ import annotations

import ctypes
import json
import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path
from types import TracebackType
from typing import Any, Self
from urllib.error import URLError
from urllib.request import urlopen

DESKTOP_HOST = "127.0.0.1"
DESKTOP_PORT = 8000
DESKTOP_URL = f"http://{DESKTOP_HOST}:{DESKTOP_PORT}"
MUTEX_NAME = r"Local\WinAssistLocalDesktop"
ERROR_ALREADY_EXISTS = 183
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 820
WINDOW_MARGIN = 24


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", _Rect),
        ("rcWork", _Rect),
        ("dwFlags", ctypes.c_ulong),
    ]


def active_monitor_work_area() -> tuple[int, int, int, int]:
    """Return the monitor work area containing the cursor, excluding its taskbar."""
    if os.name != "nt":
        return (0, 0, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    user32 = ctypes.windll.user32
    point = _Point()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return (0, 0, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    monitor = user32.MonitorFromPoint(point, 2)  # MONITOR_DEFAULTTONEAREST
    info = _MonitorInfo()
    info.cbSize = ctypes.sizeof(_MonitorInfo)
    if not monitor or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return (0, 0, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    work = info.rcWork
    return (work.left, work.top, work.right, work.bottom)


def centered_window_geometry(
    work_area: tuple[int, int, int, int],
    *,
    preferred_width: int = DEFAULT_WINDOW_WIDTH,
    preferred_height: int = DEFAULT_WINDOW_HEIGHT,
    margin: int = WINDOW_MARGIN,
) -> tuple[int, int, int, int]:
    """Fit and center a window inside a monitor work area."""
    left, top, right, bottom = work_area
    work_width = max(1, right - left)
    work_height = max(1, bottom - top)
    width = min(preferred_width, max(320, work_width - margin * 2), work_width)
    height = min(preferred_height, max(240, work_height - margin * 2), work_height)
    x = left + max(0, (work_width - width) // 2)
    y = top + max(0, (work_height - height) // 2)
    return (x, y, width, height)


def desktop_icon_path() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    bundled = bundle_root / "WinAssist.ico"
    return bundled if bundled.exists() else bundle_root / "packaging" / "WinAssist.ico"


class DesktopController:
    """Coordinates close confirmation, tray hiding and final shutdown."""

    def __init__(self) -> None:
        self.window: Any | None = None
        self.tray_available = False
        self.exit_requested = False

    def bind(self, window: Any) -> None:
        self.window = window

    def on_closing(self) -> bool:
        if self.exit_requested:
            return True
        threading.Timer(0.05, self._show_close_dialog).start()
        return False

    def _show_close_dialog(self) -> None:
        if self.window is None:
            return
        try:
            shown = self.window.evaluate_js(
                "window.WinAssistDesktop?.showCloseDialog?.() ?? false"
            )
            if shown:
                return
        except Exception:  # noqa: BLE001 - native fallback at desktop boundary
            pass
        self._native_close_fallback()

    def _native_close_fallback(self) -> None:
        if os.name != "nt":
            return
        choice = ctypes.windll.user32.MessageBoxW(
            None,
            "Bạn muốn đóng WinAssist thế nào?\n\n"
            "Có: Đóng xuống khay hệ thống\n"
            "Không: Thoát hoàn toàn\n"
            "Hủy: Quay lại ứng dụng",
            "Đóng WinAssist",
            0x23,
        )
        if choice == 6:
            self.close_to_tray()
        elif choice == 7:
            self.exit_app()

    def close_to_tray(self) -> dict[str, object]:
        if self.window is None or not self.tray_available:
            return {
                "success": False,
                "message": "Khay hệ thống chưa sẵn sàng. Bạn có thể thoát hoàn toàn.",
            }
        self.window.hide()
        return {
            "success": True,
            "message": "WinAssist vẫn đang chạy dưới khay hệ thống.",
        }

    def exit_app(self) -> dict[str, object]:
        self.exit_requested = True
        if self.window is not None:
            self.window.destroy()
        return {"success": True, "message": "Đang thoát WinAssist."}


class DesktopTray:
    def __init__(self, window: Any, controller: DesktopController) -> None:
        self.window = window
        self.controller = controller
        self.icon: Any | None = None

    def start(self) -> bool:
        try:
            import pystray
            from PIL import Image

            image = Image.open(desktop_icon_path())
            self.icon = pystray.Icon(
                "WinAssist",
                image,
                "WinAssist",
                menu=pystray.Menu(
                    pystray.MenuItem("Mở WinAssist", self._show, default=True),
                    pystray.MenuItem("Ẩn cửa sổ", self._hide),
                    pystray.MenuItem("Thoát", self._exit),
                ),
            )
            self.icon.run_detached()
            return True
        except (ImportError, OSError):
            return False

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()

    def _show(self, *_: object) -> None:
        self.window.show()

    def _hide(self, *_: object) -> None:
        self.window.hide()

    def _exit(self, *_: object) -> None:
        self.stop()
        self.controller.exit_app()


class SingleInstance:
    """Windows mutex that prevents two desktop shells from owning one backend."""

    def __init__(self, name: str = MUTEX_NAME) -> None:
        self.name = name
        self._handle: int | None = None

    def acquire(self) -> bool:
        if os.name != "nt":
            return True
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel32.CreateMutexW(None, False, self.name)
        if not handle:
            return False
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._handle = int(handle)
        return True

    def release(self) -> None:
        if self._handle is None or os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle(ctypes.c_void_p(self._handle))
        self._handle = None

    def __enter__(self) -> Self:
        if not self.acquire():
            raise RuntimeError("WinAssist đang chạy trong một cửa sổ khác.")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()


def configure_runtime_paths() -> Path:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    runtime_root = local_app_data / "WinAssist Local"
    data_dir = runtime_root / "data"
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["WINASSIST_DATABASE_PATH"] = str(data_dir / "winassist.db")
    os.environ["WINASSIST_LOG_PATH"] = str(log_dir / "winassist.jsonl")
    return runtime_root


def loopback_port_is_available(host: str = DESKTOP_HOST, port: int = DESKTOP_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


class EmbeddedBackend:
    def __init__(self, host: str = DESKTOP_HOST, port: int = DESKTOP_PORT) -> None:
        self.host = host
        self.port = port
        self.server: Any | None = None
        self.thread: threading.Thread | None = None
        self.startup_error: Exception | None = None

    def start(self) -> None:
        import uvicorn

        from app.main import app

        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(
            target=self._run_server,
            name="winassist-backend",
            daemon=True,
        )
        self.thread.start()

    def _run_server(self) -> None:
        server = self.server
        if server is None:
            self.startup_error = RuntimeError("Backend server chưa được khởi tạo.")
            return
        try:
            server.run()
        except Exception as exc:  # noqa: BLE001 - forwarded to the desktop boundary
            self.startup_error = exc

    def wait_until_ready(self, timeout_seconds: float = 15) -> bool:
        deadline = time.monotonic() + timeout_seconds
        readiness_url = f"http://{self.host}:{self.port}/api/ready"
        while time.monotonic() < deadline:
            if self.startup_error is not None:
                return False
            try:
                with urlopen(readiness_url, timeout=1) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    if response.status == 200 and payload.get("status") == "ready":
                        return True
            except (OSError, URLError, ValueError):
                time.sleep(0.15)
        return False

    def stop(self) -> None:
        if self.server is not None:
            self.server.should_exit = True
        if self.thread is not None:
            self.thread.join(timeout=5)


def show_native_error(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, "WinAssist", 0x10)
    else:
        print(message)


def launch_desktop() -> int:
    instance = SingleInstance()
    if not instance.acquire():
        show_native_error("WinAssist đang chạy trong một cửa sổ khác.")
        return 2

    backend: EmbeddedBackend | None = None
    try:
        if not loopback_port_is_available():
            show_native_error(
                "Port 8000 đang được ứng dụng khác sử dụng. "
                "Hãy đóng backend WinAssist cũ rồi mở lại ứng dụng."
            )
            return 3
        configure_runtime_paths()
        desktop_token = secrets.token_urlsafe(32)
        os.environ["WINASSIST_DESKTOP_API_TOKEN"] = desktop_token
        backend = EmbeddedBackend()
        backend.start()
        if not backend.wait_until_ready():
            detail = (
                f" ({type(backend.startup_error).__name__})"
                if backend.startup_error is not None
                else ""
            )
            show_native_error(
                f"Backend WinAssist không khởi động được{detail}. "
                "Hãy xem log trong %LOCALAPPDATA%\\WinAssist Local\\data\\logs."
            )
            return 4

        import webview

        window_x, window_y, window_width, window_height = centered_window_geometry(
            active_monitor_work_area()
        )
        controller = DesktopController()
        window = webview.create_window(
            "WinAssist",
            f"{DESKTOP_URL}/?desktop_token={desktop_token}",
            js_api=controller,
            width=window_width,
            height=window_height,
            x=window_x,
            y=window_y,
            min_size=(min(960, window_width), min(640, window_height)),
        )
        controller.bind(window)
        window.events.closing += controller.on_closing
        tray = DesktopTray(window, controller)
        controller.tray_available = tray.start()
        webview.start(gui="edgechromium", debug=False)
        tray.stop()
        return 0
    except ImportError:
        show_native_error(
            "Thiếu pywebview. Hãy cài requirements-desktop.txt rồi thử lại."
        )
        return 5
    except Exception as exc:  # noqa: BLE001 - desktop boundary must show a native error
        show_native_error(
            f"WinAssist không thể khởi động ({type(exc).__name__}). "
            "Hãy xem log trong %LOCALAPPDATA%\\WinAssist Local\\data\\logs."
        )
        return 6
    finally:
        if backend is not None:
            backend.stop()
        instance.release()


def main() -> None:
    raise SystemExit(launch_desktop())


if __name__ == "__main__":
    main()
