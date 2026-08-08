from fastapi.testclient import TestClient
import time

from app.api.software import get_software_service
from app.database.db import Database
from app.database.repositories import PendingActionRepository
from app.main import app
from app.services.software_catalog import SoftwareCatalog
from app.services.software_service import SoftwareService, registry_from_catalog
from tests.test_software_service import FakeSoftwareRunner


def service_for_api(tmp_path):
    database = Database(tmp_path / "api.db")
    database.initialize()
    catalog = SoftwareCatalog()
    registry = registry_from_catalog(catalog)
    return SoftwareService(
        PendingActionRepository(database),
        catalog=catalog,
        registry=registry,
        runner=FakeSoftwareRunner(),
    )


def test_list_check_install_confirm_flow(tmp_path) -> None:
    service = service_for_api(tmp_path)
    app.dependency_overrides[get_software_service] = lambda: service
    try:
        with TestClient(app) as client:
            listed = client.get("/api/software")
            checked = client.post(
                "/api/software/check", json={"software_id": "firefox"}
            )
            install = client.post(
                "/api/software/install", json={"software_id": "firefox"}
            )
            action_id = install.json()["pending_action"]["id"]
            confirmed = client.post(f"/api/actions/{action_id}/confirm")
            status = None
            for _ in range(20):
                status = client.get(f"/api/actions/{action_id}/status")
                if status.json()["action"]["state"] in {"completed", "failed"}:
                    break
                time.sleep(0.01)
            replayed = client.post(f"/api/actions/{action_id}/confirm")
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert len(listed.json()) == 82
    assert checked.status_code == 200
    assert checked.json()["installed"] is False
    assert install.status_code == 200
    assert install.json()["pending_action"]["state"] == "pending"
    assert confirmed.status_code == 202
    assert confirmed.json()["action"]["state"] == "executing"
    assert status is not None
    assert status.json()["action"]["state"] == "completed"
    assert replayed.status_code == 409


def test_confirm_endpoint_does_not_accept_replacement_command(tmp_path) -> None:
    service = service_for_api(tmp_path)
    app.dependency_overrides[get_software_service] = lambda: service
    try:
        with TestClient(app) as client:
            install = client.post(
                "/api/software/install", json={"software_id": "firefox"}
            )
            action_id = install.json()["pending_action"]["id"]
            response = client.post(
                f"/api/actions/{action_id}/confirm",
                json={"command_id": "software.install.vlc", "arguments": ["malicious"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["action"]["command_id"] == "software.install.firefox"


def test_unknown_software_returns_not_found(tmp_path) -> None:
    service = service_for_api(tmp_path)
    app.dependency_overrides[get_software_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/software/check", json={"software_id": "arbitrary-package"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
