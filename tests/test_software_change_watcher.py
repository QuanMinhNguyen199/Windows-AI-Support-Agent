import asyncio
import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.software_change_watcher import SoftwareChangeBroker


def test_broker_publishes_inventory_change() -> None:
    broker = SoftwareChangeBroker()
    queue = broker.subscribe()

    broker.publish("HKCU\\Software\\Uninstall")
    payload = queue.get_nowait()
    broker.unsubscribe(queue)

    assert payload["event"] == "software_inventory_changed"
    assert payload["source"] == "HKCU\\Software\\Uninstall"
    assert payload["detected_at"].endswith("+00:00")


def test_broker_sse_encoding_is_valid_json() -> None:
    encoded = SoftwareChangeBroker.encode_sse(
        "software_inventory_changed",
        {"name": "Ứng dụng"},
    )

    lines = encoded.splitlines()
    assert lines[0] == "event: software_inventory_changed"
    assert json.loads(lines[1].removeprefix("data: ")) == {"name": "Ứng dụng"}


def test_broker_drops_old_event_when_slow_subscriber() -> None:
    broker = SoftwareChangeBroker()
    queue: asyncio.Queue[dict[str, str]] = asyncio.Queue(maxsize=1)
    broker._subscribers.add(queue)

    broker.publish("first")
    broker.publish("latest")

    assert queue.get_nowait()["source"] == "latest"


def test_latest_patch_api() -> None:
    with TestClient(app) as client:
        response = client.get("/api/patches/latest")

    assert response.status_code == 200
    assert response.json()["version"] == "0.10.1"
    assert response.json()["highlights"]


def test_software_event_stream_is_exposed() -> None:
    schema = app.openapi()

    assert "/api/software/events" in schema["paths"]
