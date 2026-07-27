from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "WinAssist Local"
    app_version: str = "0.3.0"
    environment: str = "development"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    database_path: Path = BASE_DIR.parent / "data" / "winassist.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WINASSIST_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
