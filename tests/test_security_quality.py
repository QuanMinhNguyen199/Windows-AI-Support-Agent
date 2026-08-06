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


def test_api_client_drives_global_loading_without_fake_percentage() -> None:
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    source = Path("app/static/api-client.js").read_text(encoding="utf-8")

    assert 'id="global-loading"' in html
    assert "beginLoading();" in source
    assert "endLoading();" in source
    assert "percent" not in source.casefold()


def test_sidebar_labels_stay_on_one_line_and_scrollbar_reaches_edge() -> None:
    css = Path("app/static/overview.css").read_text(encoding="utf-8")

    assert "grid-template-columns: 260px minmax(0, 1fr)" in css
    assert "white-space: nowrap" in css
    assert "padding: 28px 0 18px 18px" in css


def test_successful_request_is_not_stored_in_debug_log() -> None:
    marker = "SHOULD_NOT_APPEAR_IN_LOG"
    with TestClient(app) as client:
        response = client.get(f"/?token={marker}")

    assert response.status_code == 200
    log_text = Path("data/logs/debug-errors.jsonl").read_text(encoding="utf-8")
    assert marker not in log_text
    assert '"status_code": 200' not in log_text


def test_silent_update_preserves_desktop_shortcut() -> None:
    installer = Path("packaging/WinAssist.iss").read_text(encoding="utf-8")
    desktop = Path("app/desktop.py").read_text(encoding="utf-8")

    assert "ShouldCreateDesktopShortcut" in installer
    assert "/MERGETASKS=desktopicon" in desktop
