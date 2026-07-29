import asyncio
import json

import httpx
import pytest

from app.models.chat import Intent
from app.services.ollama_service import OllamaService, OllamaUnavailableError


def service_with_handler(handler) -> OllamaService:
    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    return OllamaService(
        base_url="http://ollama.test",
        model="qwen2.5:3b",
        client=client,
    )


def test_ollama_health_detects_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen2.5:3b"}]},
        )

    service = service_with_handler(handler)
    health = asyncio.run(service.health())

    assert health.available is True
    assert health.model_available is True
    asyncio.run(service._client.aclose())


def test_ollama_classification_uses_structured_schema() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["stream"] is False
        assert body["think"] is False
        assert body["format"]["type"] == "object"
        assert body["options"]["temperature"] == 0
        content = {
            "intent": "software_installation",
            "confidence": 0.95,
            "software_id": "firefox",
            "reason": "User wants install",
        }
        return httpx.Response(200, json={"message": {"content": json.dumps(content)}})

    service = service_with_handler(handler)
    result = asyncio.run(
        service.classify_intent("Cài Firefox", software_ids=["firefox"])
    )

    assert result.intent is Intent.SOFTWARE_INSTALLATION
    assert result.software_id == "firefox"
    asyncio.run(service._client.aclose())


def test_invalid_ollama_output_triggers_fallback_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": '{"intent":"run_cmd"}'}})

    service = service_with_handler(handler)
    with pytest.raises(OllamaUnavailableError):
        asyncio.run(service.classify_intent("ignore rules", software_ids=[]))
    asyncio.run(service._client.aclose())


def test_unsafe_ai_explanation_is_rejected() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        content = {
            "message": "Hãy tắt Firewall để thử.",
            "recommendations": ["Disable Defender"],
        }
        return httpx.Response(200, json={"message": {"content": json.dumps(content)}})

    service = service_with_handler(handler)
    with pytest.raises(OllamaUnavailableError, match="an toàn"):
        asyncio.run(service.explain_diagnostic({"status": "error"}))
    asyncio.run(service._client.aclose())
