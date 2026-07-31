from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_are_added_to_frontend() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )
    assert response.headers["x-request-id"]


def test_frontend_does_not_render_untrusted_html() -> None:
    source = Path("app/static/app.js").read_text(encoding="utf-8")

    assert ".innerHTML" not in source
    assert "insertAdjacentHTML" not in source
    assert "document.write" not in source


def test_request_log_does_not_store_query_string() -> None:
    marker = "SHOULD_NOT_APPEAR_IN_LOG"
    with TestClient(app) as client:
        response = client.get(f"/?token={marker}")

    assert response.status_code == 200
    log_text = Path("data/logs/winassist.jsonl").read_text(encoding="utf-8")
    assert marker not in log_text
