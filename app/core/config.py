from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_KEY: str

    CORS_ALLOWED_ORIGINS: list[str] = []

    GEMINI_API_KEY: str | None = None
    # Second Gemini key (separate project/quota) tried right after the
    # primary one - same GEMINI_MODEL.
    GEMINI_API_KEY_BACKUP: str | None = None
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None

    # Model ids come only from the environment - no hardcoded defaults.
    # Each one is required as soon as its provider's API key is set.
    GEMINI_MODEL: str | None = None
    GROQ_MODEL: str | None = None
    OPENROUTER_MODEL: str | None = None
    MISTRAL_MODEL: str | None = None

    # OpenAI-compatible JSON mode (`response_format: json_object`).
    # Some free OpenRouter models reject this and return HTTP 400 - set the
    # matching flag to false to omit it (prompt + extract_json_object still
    # enforce JSON).
    AI_RESPONSE_FORMAT_JSON: bool = True
    OPENROUTER_JSON_OBJECT: bool = True

    AI_TIMEOUT_SECONDS: float = 20.0
    AI_PROVIDER_MODE: Literal["chain", "stub"] = "chain"
    AI_LOG_METRICS: bool = True

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

    @model_validator(mode="after")
    def _require_model_for_each_configured_key(self) -> "Settings":
        key_to_model = {
            "GEMINI_API_KEY": "GEMINI_MODEL",
            "GEMINI_API_KEY_BACKUP": "GEMINI_MODEL",
            "GROQ_API_KEY": "GROQ_MODEL",
            "MISTRAL_API_KEY": "MISTRAL_MODEL",
            "OPENROUTER_API_KEY": "OPENROUTER_MODEL",
        }
        missing = sorted(
            {
                model
                for key, model in key_to_model.items()
                if getattr(self, key) and not getattr(self, model)
            }
        )
        if missing:
            raise ValueError(
                f"{', '.join(missing)} must be set when the matching API key is "
                "configured"
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
