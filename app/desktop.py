from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self
from urllib.error import URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from app.core.model_selection import select_ollama_model

DESKTOP_HOST = "127.0.0.1"
DESKTOP_PORT = 8000
DESKTOP_URL = f"http://{DESKTOP_HOST}:{DESKTOP_PORT}"
MUTEX_NAME = r"Local\WinAssistLocalDesktop"
ERROR_ALREADY_EXISTS = 183
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 820
WINDOW_MARGIN = 24


def write_desktop_crash_log(exc: BaseException) -> Path:
    log_dir = (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        / "WinAssist Local"
        / "data"
        / "logs"
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "desktop-crash.log"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n[{datetime.now(UTC).isoformat()}] {type(exc).__name__}: {exc}\n")
        stream.write("".join(traceback.format_exception(exc)))
    return path


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


def installed_uninstaller_path() -> Path | None:
    """Return the trusted Inno uninstaller beside the frozen desktop executable."""
    if not getattr(sys, "frozen", False):
        return None
    install_dir = Path(sys.executable).resolve().parent
    candidate = (install_dir / "unins000.exe").resolve()
    if candidate.parent != install_dir or candidate.name.casefold() != "unins000.exe":
        return None
    return candidate if candidate.is_file() else None


def delayed_uninstall_command(uninstaller: Path, process_id: int) -> list[str]:
    """Build a detached Windows command that uninstalls only after WinAssist exits."""
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    escaped_uninstaller = str(uninstaller).replace("'", "''")
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Wait-Process -Id {process_id};"
        f"Start-Process -FilePath '{escaped_uninstaller}' "
        "-ArgumentList @('/SILENT','/SUPPRESSMSGBOXES','/NORESTART','/PURGEDATA=1') "
        "-Wait"
    )
    encoded_script = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return [
        str(powershell),
        "-NoProfile",
        "-NonInteractive",
        "-WindowStyle",
        "Hidden",
        "-EncodedCommand",
        encoded_script,
    ]


def delayed_update_command(installer: Path, process_id: int) -> list[str]:
    """Run a verified Inno update silently after the current app has exited."""
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    escaped_installer = str(installer).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop';"
        f"Wait-Process -Id {process_id} -ErrorAction SilentlyContinue;"
        f"$setup=Start-Process -FilePath '{escaped_installer}' "
        "-ArgumentList @('/VERYSILENT','/SP-','/SUPPRESSMSGBOXES','/NORESTART',"
        "'/CLOSEAPPLICATIONS','/MERGETASKS=desktopicon','/UPDATE=1') -Wait -PassThru;"
        "if($setup.ExitCode -ne 0){exit $setup.ExitCode}"
    )
    encoded_script = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return [
        str(powershell),
        "-NoProfile",
        "-NonInteractive",
        "-WindowStyle",
        "Hidden",
        "-EncodedCommand",
        encoded_script,
    ]


class DesktopUpdater:
    """Download and verify a trusted WinAssist installer outside the AI agent."""

    _VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
    _SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
    _RELEASE_PATH = "/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/download/"
    _MAX_INSTALLER_BYTES = 512 * 1024 * 1024

    def __init__(self, *, runtime_root: Path | None = None, available: bool | None = None) -> None:
        self.runtime_root = runtime_root or (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "WinAssist Local"
        )
        self.available = bool(getattr(sys, "frozen", False)) if available is None else available
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None
        self._installer: Path | None = None
        self._expected_sha256: str | None = None
        self._metadata = self.runtime_root / "updates" / "pending-update.json"
        self._state: dict[str, object] = {
            "state": "idle",
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "percent": 0,
            "message": "Sẵn sàng kiểm tra cập nhật.",
        }

    def status(self) -> dict[str, object]:
        with self._lock:
            return {"available": self.available, **self._state}

    def start(self, url: str, version: str, sha256: str) -> dict[str, object]:
        if not self.available:
            return {"success": False, "message": "Chỉ có thể cập nhật trong bản WinAssist đã cài."}
        try:
            self._validate_release(url, version, sha256)
        except ValueError as exc:
            return {"success": False, "message": str(exc)}
        with self._lock:
            if self._state["state"] in {"downloading", "installing"}:
                return {"success": False, "message": "Một bản cập nhật đang được xử lý."}
            update_dir = (self.runtime_root / "updates").resolve()
            update_dir.mkdir(parents=True, exist_ok=True)
            self._installer = update_dir / f"WinAssist-{version}-Setup.exe"
            self._expected_sha256 = sha256.lower()
            self._metadata.write_text(
                json.dumps(
                    {
                        "url": url,
                        "version": version,
                        "sha256": self._expected_sha256,
                        "installer": str(self._installer),
                    }
                ),
                encoding="utf-8",
            )
            self._cancel.clear()
            self._state = {
                "state": "downloading",
                "version": version,
                "downloaded_bytes": 0,
                "total_bytes": 0,
                "percent": 0,
                "message": "Đang tải bản cập nhật…",
            }
            self._thread = threading.Thread(
                target=self._download,
                args=(url,),
                name="winassist-updater",
                daemon=True,
            )
            self._thread.start()
        return {"success": True, "message": "Đã bắt đầu tải bản cập nhật."}

    def resume_pending(self) -> None:
        """Resume an interrupted download left by a previous app shutdown."""
        if not self.available or not self._metadata.is_file():
            return
        try:
            pending = json.loads(self._metadata.read_text(encoding="utf-8"))
            url = str(pending["url"])
            version = str(pending["version"])
            expected = str(pending["sha256"])
            installer = Path(str(pending["installer"])).resolve()
            self._validate_release(url, version, expected)
            update_dir = (self.runtime_root / "updates").resolve()
            if installer.parent != update_dir or not installer.name.endswith("-Setup.exe"):
                return
            temporary = installer.with_suffix(installer.suffix + ".part")
            if not temporary.is_file() or temporary.stat().st_size == 0:
                return
            with self._lock:
                if self._state["state"] != "idle":
                    return
                self._installer = installer
                self._expected_sha256 = expected.lower()
                self._state.update(
                    state="downloading",
                    version=version,
                    downloaded_bytes=temporary.stat().st_size,
                    total_bytes=0,
                    percent=0,
                    message="Đang tiếp tục tải bản cập nhật…",
                )
                self._thread = threading.Thread(
                    target=self._download,
                    args=(url,),
                    name="winassist-updater-resume",
                    daemon=True,
                )
                self._thread.start()
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return

    def cancel(self) -> dict[str, object]:
        with self._lock:
            if self._state["state"] != "downloading":
                return {"success": False, "message": "Không có bản cập nhật đang tải."}
            self._state["message"] = "Đang hủy tải xuống…"
        self._cancel.set()
        return {"success": True, "message": "Đang hủy tải xuống…"}

    def install(self) -> dict[str, object]:
        with self._lock:
            installer = self._installer
            expected = self._expected_sha256
            if self._state["state"] != "ready" or installer is None or expected is None:
                return {"success": False, "message": "Bản cập nhật chưa tải xong."}
        if not installer.is_file() or self._file_sha256(installer) != expected:
            self._set_state("failed", "File cập nhật không còn hợp lệ. Hãy tải lại.")
            return {"success": False, "message": "File cập nhật không còn hợp lệ. Hãy tải lại."}
        try:
            subprocess.Popen(  # noqa: S603 - verified installer from the official release
                delayed_update_command(installer, os.getpid()),
                shell=False,
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError:
            self._set_state("failed", "Không thể mở trình cập nhật.")
            return {"success": False, "message": "Không thể mở trình cập nhật."}
        self._set_state("installing", "WinAssist sẽ tự khởi động lại để hoàn tất cập nhật…")
        self._metadata.unlink(missing_ok=True)
        return {"success": True, "message": "WinAssist đang tự cập nhật và sẽ mở lại."}

    def _download(self, url: str) -> None:
        installer = self._installer
        expected = self._expected_sha256
        if installer is None or expected is None:
            return
        temporary = installer.with_suffix(installer.suffix + ".part")
        try:
            resume_from = temporary.stat().st_size if temporary.exists() else 0
            headers = {"User-Agent": "WinAssist-Updater"}
            if resume_from:
                headers["Range"] = f"bytes={resume_from}-"
            request = Request(url, headers=headers)
            with urlopen(request, timeout=30) as response:
                response_status = getattr(response, "status", None)
                if response_status is None:
                    getcode = getattr(response, "getcode", None)
                    response_status = getcode() if callable(getcode) else 200
                is_resume = resume_from > 0 and response_status == 206
                if not is_resume:
                    resume_from = 0
                total_length = int(response.headers.get("Content-Length") or 0)
                total = total_length + resume_from if is_resume else total_length
                if total > self._MAX_INSTALLER_BYTES:
                    raise ValueError("Gói cập nhật lớn bất thường")
                digest = hashlib.sha256()
                downloaded = resume_from
                if resume_from:
                    with temporary.open("rb") as existing:
                        for previous in iter(lambda: existing.read(1024 * 1024), b""):
                            digest.update(previous)
                with temporary.open("ab" if is_resume else "wb") as stream:
                    started_at = time.perf_counter()
                    while True:
                        if self._cancel.is_set():
                            raise InterruptedError
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        stream.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)
                        if downloaded > self._MAX_INSTALLER_BYTES:
                            raise ValueError("Gói cập nhật lớn bất thường")
                        percent = round(downloaded * 100 / total) if total else 0
                        elapsed = max(time.perf_counter() - started_at, 0.001)
                        speed = (downloaded - resume_from) / elapsed / (1024 * 1024)
                        progress_message = (
                            f"Đang tải bản cập nhật… {downloaded / (1024 * 1024):.1f} MB"
                            + (f" / {total / (1024 * 1024):.1f} MB · {speed:.1f} MB/s" if total else "")
                        )
                        with self._lock:
                            self._state.update(
                                downloaded_bytes=downloaded,
                                total_bytes=total,
                                percent=min(percent, 100),
                                message=progress_message,
                            )
            if digest.hexdigest().lower() != expected:
                raise ValueError("SHA-256 không khớp")
            os.replace(temporary, installer)
            self._metadata.unlink(missing_ok=True)
            self._set_state("ready", "Đã tải và kiểm tra an toàn. Sẵn sàng cập nhật.", percent=100)
        except InterruptedError:
            temporary.unlink(missing_ok=True)
            self._metadata.unlink(missing_ok=True)
            self._set_state("cancelled", "Đã hủy tải bản cập nhật.")
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            temporary.unlink(missing_ok=True)
            self._set_state("failed", f"Không thể tải bản cập nhật: {exc}")

    def _validate_release(self, url: str, version: str, sha256: str) -> None:
        parsed = urlparse(url)
        filename = Path(unquote(parsed.path)).name
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or self._RELEASE_PATH not in parsed.path
            or not filename.casefold().endswith("-setup.exe")
        ):
            raise ValueError("Link cập nhật không thuộc GitHub chính thức của WinAssist.")
        if not self._VERSION_PATTERN.fullmatch(version):
            raise ValueError("Phiên bản cập nhật không hợp lệ.")
        if not self._SHA256_PATTERN.fullmatch(sha256):
            raise ValueError("Bản cập nhật chưa có mã kiểm tra an toàn.")

    def _set_state(self, state: str, message: str, **values: object) -> None:
        with self._lock:
            self._state.update(state=state, message=message, **values)

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(128 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().lower()


class LocalAiInstaller:
    """Install Ollama and its selected model from the native WinAssist window."""

    _OLLAMA_URL = "https://ollama.com/download/OllamaSetup.exe"
    _MAX_INSTALLER_BYTES = 512 * 1024 * 1024

    def __init__(self, *, runtime_root: Path | None = None) -> None:
        self.runtime_root = runtime_root or (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "WinAssist Local"
        )
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._state: dict[str, object] = {
            "state": "idle",
            "model": select_ollama_model(),
            "percent": 0,
            "message": "Local AI chưa được cài.",
        }

    def status(self) -> dict[str, object]:
        with self._lock:
            result = dict(self._state)
        installed = self._ollama_executable() is not None
        result["installed"] = installed
        if result["state"] == "idle":
            result["message"] = (
                "Ollama đã được cài nhưng chưa sẵn sàng."
                if installed
                else "Local AI chưa được cài."
            )
        return result

    def start(self) -> dict[str, object]:
        with self._lock:
            if self._state["state"] in {"downloading", "installing", "pulling"}:
                return {"success": False, "message": "Local AI đang được cài."}
            installed = self._ollama_executable() is not None
            self._state.update(
                state="installing" if installed else "downloading",
                percent=40 if installed else 0,
                message=(
                    "Đã tìm thấy Ollama. Đang chuẩn bị model…"
                    if installed
                    else "Đang tải bộ cài Local AI…"
                ),
            )
            self._thread = threading.Thread(
                target=self._install,
                name="winassist-local-ai-installer",
                daemon=True,
            )
            self._thread.start()
        return {"success": True, "message": "Đã bắt đầu cài Local AI."}

    def _install(self) -> None:
        installer = self.runtime_root / "local-ai" / "OllamaSetup.exe"
        temporary = installer.with_suffix(".part")
        model = str(self._state["model"])
        try:
            executable = self._ollama_executable()
            if executable is None:
                installer.parent.mkdir(parents=True, exist_ok=True)
                request = Request(self._OLLAMA_URL, headers={"User-Agent": "WinAssist"})
                with urlopen(request, timeout=30) as response, temporary.open("wb") as stream:
                    total = int(response.headers.get("Content-Length") or 0)
                    downloaded = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        stream.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > self._MAX_INSTALLER_BYTES:
                            raise ValueError("Bộ cài Local AI lớn bất thường.")
                        self._set_state(
                            percent=round(downloaded * 35 / total) if total else 0,
                            message="Đang tải bộ cài Local AI…",
                        )
                os.replace(temporary, installer)
                self._set_state(state="installing", percent=40, message="Đang cài Ollama…")
                completed = subprocess.run(
                    [str(installer), "/VERYSILENT", "/NORESTART"],
                    shell=False,
                    capture_output=True,
                    timeout=300,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if completed.returncode != 0:
                    raise RuntimeError("Bộ cài Ollama trả về mã lỗi.")
                executable = self._ollama_executable()
                if executable is None:
                    raise RuntimeError("Không tìm thấy Ollama sau khi cài.")
            subprocess.Popen(
                [str(executable), "serve"],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            self._set_state(state="pulling", percent=50, message="Đang chuẩn bị trợ lý AI…")
            pulled = None
            for attempt in range(5):
                pulled = subprocess.run(
                    [str(executable), "pull", model],
                    shell=False,
                    capture_output=True,
                    timeout=1800,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if pulled.returncode == 0 or attempt == 4:
                    break
                time.sleep(2)
            if pulled.returncode != 0:
                raise RuntimeError("Không tải được model Local AI.")
            self._set_state(state="ready", percent=100, message="Trợ lý AI đã sẵn sàng.")
        except (OSError, URLError, TimeoutError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            temporary.unlink(missing_ok=True)
            self._set_state(state="failed", message=f"Không thể cài Local AI: {exc}")

    @staticmethod
    def _ollama_executable() -> Path | None:
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Ollama" / "ollama.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        on_path = shutil.which("ollama")
        if on_path:
            return Path(on_path).resolve()
        return None

    def _set_state(self, **values: object) -> None:
        with self._lock:
            self._state.update(values)


class DesktopController:
    """Coordinates close confirmation, tray hiding and final shutdown."""

    def __init__(self, updater: DesktopUpdater | None = None, local_ai: LocalAiInstaller | None = None) -> None:
        # Keep native objects private. pywebview inspects public js_api members and
        # recursively walking a Window reaches WinForms Font/Families/SyncRoot.
        self._window: Any | None = None
        self.tray_available = False
        self.exit_requested = False
        self._close_dialog_pending = False
        self._updater = updater or DesktopUpdater()
        self._local_ai = local_ai or LocalAiInstaller()
        self._updater.resume_pending()

    def bind(self, window: Any) -> None:
        self._window = window

    def on_closing(self) -> bool:
        if self.exit_requested:
            return True
        if not self._close_dialog_pending:
            self._close_dialog_pending = True
            # The closing callback runs on the native UI thread. Evaluating JS
            # synchronously here displays the modal but blocks all its clicks.
            threading.Timer(0.05, self._show_close_dialog).start()
        return False

    def _show_close_dialog(self) -> None:
        try:
            if self._window is None:
                return
            shown = self._window.evaluate_js(
                "window.WinAssistDesktop?.showCloseDialog?.() ?? false"
            )
            if shown:
                return
        except Exception:  # noqa: BLE001 - keep the app open if UI is not ready
            return
        finally:
            self._close_dialog_pending = False

    def close_to_tray(self) -> dict[str, object]:
        if self._window is None or not self.tray_available:
            return {
                "success": False,
                "message": "Khay hệ thống chưa sẵn sàng. Bạn có thể thoát hoàn toàn.",
            }
        self._window.hide()
        return {
            "success": True,
            "message": "WinAssist vẫn đang chạy dưới khay hệ thống.",
        }

    def exit_app(self) -> dict[str, object]:
        self.exit_requested = True
        if self._window is not None:
            self._window.destroy()
        return {"success": True, "message": "Đang thoát WinAssist."}

    def uninstall_status(self) -> dict[str, object]:
        available = installed_uninstaller_path() is not None
        return {
            "available": available,
            "message": (
                "WinAssist đã sẵn sàng để gỡ khỏi máy."
                if available
                else "Chỉ có thể gỡ WinAssist từ bản đã cài bằng Setup."
            ),
        }

    def uninstall_app(self) -> dict[str, object]:
        uninstaller = installed_uninstaller_path()
        if uninstaller is None:
            return {
                "success": False,
                "message": "Không tìm thấy bộ gỡ cài đặt WinAssist hợp lệ.",
            }
        try:
            subprocess.Popen(  # noqa: S603 - fixed system helper and trusted uninstaller
                delayed_uninstall_command(uninstaller, os.getpid()),
                shell=False,
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError:
            return {
                "success": False,
                "message": "Không thể mở bộ gỡ cài đặt. Hãy thử lại sau.",
            }
        self.exit_app()
        return {
            "success": True,
            "message": "Đang đóng và gỡ WinAssist khỏi máy.",
        }

    def update_status(self) -> dict[str, object]:
        return self._updater.status()

    def start_update(self, url: str, version: str, sha256: str) -> dict[str, object]:
        return self._updater.start(url, version, sha256)

    def cancel_update(self) -> dict[str, object]:
        return self._updater.cancel()

    def install_update(self) -> dict[str, object]:
        result = self._updater.install()
        if result["success"]:
            self.exit_app()
        return result

    def local_ai_status(self) -> dict[str, object]:
        return self._local_ai.status()

    def install_local_ai(self) -> dict[str, object]:
        return self._local_ai.start()


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
    os.environ["WINASSIST_LOG_PATH"] = str(log_dir / "debug-errors.jsonl")
    return runtime_root


def loopback_port_is_available(host: str = DESKTOP_HOST, port: int = DESKTOP_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def embedded_uvicorn_config(app: Any, host: str, port: int) -> Any:
    """Create a server config that also works in a windowed PyInstaller build."""
    import uvicorn

    return uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
        # A windowed executable has no stdout/stderr. Uvicorn's default formatter
        # calls isatty() on stderr and otherwise crashes before the UI can open.
        log_config=None,
    )


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

        config = embedded_uvicorn_config(app, host=self.host, port=self.port)
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
        write_desktop_crash_log(exc)
        show_native_error(
            f"WinAssist không thể khởi động ({type(exc).__name__}). "
            "Hãy xem desktop-crash.log trong "
            "%LOCALAPPDATA%\\WinAssist Local\\data\\logs."
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
