import json
from functools import lru_cache
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.models.chat import (
    AIExplanation,
    IntentClassification,
    OllamaHealth,
)
from app.services.prompt_service import PromptService


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot provide a valid, schema-checked response."""


class OllamaService:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 8,
        prompt_service: PromptService | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.prompts = prompt_service or PromptService()
        self._client = client

    async def health(self) -> OllamaHealth:
        try:
            payload = await self._request("GET", "/api/tags")
            models = payload.get("models", [])
            names = {
                str(item.get("name") or item.get("model"))
                for item in models
                if isinstance(item, dict)
            }
            model_available = self.model in names
            detail = (
                f"Ollama hoạt động và model {self.model} đã sẵn sàng."
                if model_available
                else f"Ollama hoạt động nhưng chưa có model {self.model}."
            )
            return OllamaHealth(
                available=True,
                model_available=model_available,
                model=self.model,
                detail=detail,
            )
        except OllamaUnavailableError as exc:
            return OllamaHealth(
                available=False,
                model_available=False,
                model=self.model,
                detail=str(exc),
            )

    async def classify_intent(
        self,
        message: str,
        *,
        software_ids: list[str],
    ) -> IntentClassification:
        system = self.prompts.load("system/windows_assistant_v1.txt")
        task = self.prompts.load("tasks/intent_classification_v1.txt")
        user_content = (
            f"{task}\n\nSoftware ID hợp lệ: {json.dumps(software_ids)}\n\n"
            f"Nội dung người dùng:\n{message}"
        )
        payload = await self._chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            schema=IntentClassification.model_json_schema(),
        )
        try:
            result = IntentClassification.model_validate_json(payload)
        except ValidationError as exc:
            raise OllamaUnavailableError(
                "Ollama trả về intent không đúng schema."
            ) from exc
        if result.software_id and result.software_id not in software_ids:
            result.software_id = None
            result.confidence = min(result.confidence, 0.5)
        return result

    async def explain_diagnostic(self, evidence: dict[str, Any]) -> AIExplanation:
        system = self.prompts.load("system/windows_assistant_v1.txt")
        task = self.prompts.load("tool_results/diagnostic_explanation_v1.txt")
        serialized = json.dumps(evidence, ensure_ascii=False, default=str)
        payload = await self._chat(
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"{task}\n\nEvidence JSON:\n{serialized[:12_000]}",
                },
            ],
            schema=AIExplanation.model_json_schema(),
        )
        try:
            explanation = AIExplanation.model_validate_json(payload)
        except ValidationError as exc:
            raise OllamaUnavailableError(
                "Ollama trả về giải thích không đúng schema."
            ) from exc
        combined = " ".join(
            [explanation.message, *explanation.recommendations]
        ).casefold()
        unsafe_markers = (
            "tắt firewall",
            "tat firewall",
            "disable firewall",
            "tắt defender",
            "tat defender",
            "disable defender",
            "netsh winsock reset",
            "netsh int ip reset",
            "sửa registry",
            "regedit",
            "gỡ driver",
        )
        if any(marker in combined for marker in unsafe_markers):
            raise OllamaUnavailableError("Ollama trả về hướng dẫn vượt chính sách an toàn.")
        return explanation

    async def _chat(
        self,
        *,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
    ) -> str:
        response = await self._request(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0},
            },
        )
        try:
            content = response["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise OllamaUnavailableError("Ollama response thiếu message.content.") from exc
        if not isinstance(content, str) or not content.strip():
            raise OllamaUnavailableError("Ollama response rỗng.")
        return content

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        try:
            if self._client is not None:
                response = await self._client.request(method, path, **kwargs)
            else:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=self.timeout_seconds,
                    trust_env=False,
                ) as client:
                    response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise OllamaUnavailableError("Ollama response không phải JSON object.")
            return payload
        except OllamaUnavailableError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaUnavailableError(
                "Không thể kết nối hoặc đọc phản hồi từ Ollama."
            ) from exc


@lru_cache
def get_ollama_service() -> OllamaService:
    settings = get_settings()
    return OllamaService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
