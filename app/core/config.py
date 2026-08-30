from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_KEY: str

    CORS_ALLOWED_ORIGINS: list[str] = []

    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    AI_TIMEOUT_SECONDS: float = 20.0
    AI_PROVIDER_MODE: Literal["chain", "stub"] = "chain"

    LOG_LEVEL: str = "INFO"

    RATE_LIMIT: str = "60/minute"
    REDIS_URL: str | None = None

    MAX_REQUEST_BODY_BYTES: int = 262_144

    # RAG (Fase 1 - keyword search over app/knowledge/, no vector store).
    # Applies only to /lookup. Off in tests so the stub-provider fixtures
    # stay deterministic regardless of the knowledge corpus.
    RAG_ENABLED: bool = True
    RAG_MAX_CHUNKS: int = 5
    KNOWLEDGE_DIR: Path = Path("app/knowledge")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
