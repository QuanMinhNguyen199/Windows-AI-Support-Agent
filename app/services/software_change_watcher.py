from __future__ import annotations

import asyncio
import ctypes
import json
import os
import threading
from datetime import UTC, datetime
from typing import Any

UNINSTALL_REGISTRY_PATHS = (
    ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKCU", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
)


class SoftwareChangeBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, str]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, str]]:
        queue: asyncio.Queue[dict[str, str]] = asyncio.Queue(maxsize=4)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, str]]) -> None:
        self._subscribers.discard(queue)

    def publish(self, source: str) -> None:
        payload = {
            "event": "software_inventory_changed",
            "source": source,
            "detected_at": datetime.now(UTC).isoformat(),
        }
        for queue in tuple(self._subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(payload)

    @staticmethod
    def encode_sse(event: str, payload: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


class RegistrySoftwareWatcher:
    """Read-only watcher for Add/Remove Programs registry entries."""

    def __init__(
        self,
        broker: SoftwareChangeBroker,
        *,
        debounce_seconds: float = 1.5,
    ) -> None:
        self.broker = broker
        self.debounce_seconds = debounce_seconds
        self.available = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._pending: asyncio.TimerHandle | None = None

    def start(self, loop: asyncio.AbstractEventLoop) -> bool:
        if os.name != "nt" or self._threads:
            return self.available
        self._loop = loop
        self._stop = threading.Event()
        stop_event = self._stop
        for hive_name, path in UNINSTALL_REGISTRY_PATHS:
            thread = threading.Thread(
                target=self._watch_key,
                args=(hive_name, path, stop_event),
                name=f"software-registry-{hive_name.lower()}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)
        self.available = True
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._pending is not None:
            self._pending.cancel()
            self._pending = None
        # Threads are daemonized because the Windows notification call blocks until
        # the registry changes. They observe the stop flag before publishing again.
        self._threads.clear()
        self.available = False

    def notify_for_test(self, source: str = "test") -> None:
        self._schedule_change(source)

    def _watch_key(
        self,
        hive_name: str,
        path: str,
        stop_event: threading.Event,
    ) -> None:
        try:
            import winreg

            hive = winreg.HKEY_LOCAL_MACHINE if hive_name == "HKLM" else winreg.HKEY_CURRENT_USER
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_NOTIFY)
        except OSError:
            return

        notify: Any = ctypes.windll.advapi32.RegNotifyChangeKeyValue
        notify.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        notify.restype = ctypes.c_long
        filter_flags = 0x00000001 | 0x00000004  # key name or last-set value
        with key:
            while not stop_event.is_set():
                result = notify(ctypes.c_void_p(int(key)), True, filter_flags, None, False)
                if result != 0 or stop_event.is_set():
                    return
                if self._loop is not None:
                    source = f"{hive_name}\\{path}"
                    self._loop.call_soon_threadsafe(self._schedule_change, source)

    def _schedule_change(self, source: str) -> None:
        if self._loop is None:
            return
        if self._pending is not None:
            self._pending.cancel()
        self._pending = self._loop.call_later(
            self.debounce_seconds,
            self.broker.publish,
            source,
        )


software_change_broker = SoftwareChangeBroker()
software_registry_watcher = RegistrySoftwareWatcher(software_change_broker)
