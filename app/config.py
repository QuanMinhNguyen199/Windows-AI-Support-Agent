from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.model_selection import select_ollama_model

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "WinAssist Local"
    app_version: str = "0.11.3.1"
    environment: str = "development"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "auto"
    ollama_timeout_seconds: float = 3
    database_path: Path = BASE_DIR.parent / "data" / "winassist.db"
    log_path: Path = BASE_DIR.parent / "data" / "logs" / "debug-errors.jsonl"
    desktop_api_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WINASSIST_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_automatic_model(self) -> "Settings":
        if self.ollama_model.casefold() == "auto":
            self.ollama_model = select_ollama_model()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
