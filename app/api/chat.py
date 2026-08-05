from functools import lru_cache

from fastapi import APIRouter, Depends

from agents.assistant_agent import AssistantAgent
from app.api.diagnostics import get_network_service, get_speedtest_provider
from app.api.software import get_software_service
from app.api.windows import get_windows_support_service
from app.config import get_settings
from app.core.intent_router import RuleBasedIntentRouter
from app.database.db import Database
from app.database.repositories import ChatRepository
from app.models.chat import ChatRequest, ChatResponse
from app.services.ollama_service import get_ollama_service


router = APIRouter(prefix="/api", tags=["chat"])


@lru_cache
def get_assistant_agent() -> AssistantAgent:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    software = get_software_service()
    return AssistantAgent(
        router=RuleBasedIntentRouter(catalog=software.catalog),
        ollama=get_ollama_service(),
        software=software,
        network=get_network_service(),
        chat_repository=ChatRepository(database),
        speedtest=get_speedtest_provider(),
        windows=get_windows_support_service(),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: AssistantAgent = Depends(get_assistant_agent),
) -> ChatResponse:
    return await agent.handle(
        request.message,
        session_id=request.session_id,
        language=request.language,
    )
