from fastapi.testclient import TestClient

from app.api.chat import get_assistant_agent
from app.main import app
from app.models.chat import ChatResponse, Intent, RouterSource


class FakeAgent:
    async def handle(self, message: str, *, session_id: str | None = None):
        return ChatResponse(
            session_id=session_id or "00000000-0000-0000-0000-000000000001",
            intent=Intent.HELP,
            message=f"Đã nhận: {message}",
            router_source=RouterSource.RULE_BASED,
        )


def test_chat_api_returns_structured_response() -> None:
    app.dependency_overrides[get_assistant_agent] = lambda: FakeAgent()
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "Trợ giúp"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["intent"] == "help"
    assert response.json()["message"] == "Đã nhận: Trợ giúp"


def test_chat_api_rejects_empty_or_oversized_message() -> None:
    with TestClient(app) as client:
        empty = client.post("/api/chat", json={"message": ""})
        oversized = client.post("/api/chat", json={"message": "x" * 2001})

    assert empty.status_code == 422
    assert oversized.status_code == 422
