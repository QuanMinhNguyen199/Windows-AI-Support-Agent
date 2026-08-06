import json
import logging

from app.core.logging_config import configure_local_logging


def test_debug_log_ignores_success_and_redacts_error_details(tmp_path) -> None:
    logger = logging.getLogger("winassist-test-errors")
    logger.handlers.clear()
    path = tmp_path / "debug-errors.jsonl"

    # Use the production configurator with its isolated production logger name.
    production = logging.getLogger("winassist")
    old_handlers = list(production.handlers)
    production.handlers.clear()
    try:
        configured = configure_local_logging(path)
        configured.info("successful_action", extra={"status_code": 200})
        configured.error(
            "action_failed",
            extra={"error_detail": r"C:\Users\Alice\Temp\x password=secret"},
        )
        for handler in configured.handlers:
            handler.flush()
    finally:
        for handler in production.handlers:
            handler.close()
        production.handlers = old_handlers

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event"] == "action_failed"
    assert "Alice" not in payload["error_detail"]
    assert "secret" not in payload["error_detail"]
