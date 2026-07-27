from fastapi.testclient import TestClient

from app.api.health import get_ollama_service
from app.main import app
from app.models.chat import OllamaHealth


class HealthyOllama:
    async def health(self) -> OllamaHealth:
        return OllamaHealth(
            available=True,
            model_available=True,
            model="qwen2.5:3b",
            detail="ready",
        )


def test_health_check() -> None:
    app.dependency_overrides[get_ollama_service] = lambda: HealthyOllama()
    try:
        with TestClient(app) as client:
            response = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["application"] == "WinAssist Local"
    assert body["ollama"]["status"] == "available"


def test_root_serves_chat_ui() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "WinAssist Local" in response.text
