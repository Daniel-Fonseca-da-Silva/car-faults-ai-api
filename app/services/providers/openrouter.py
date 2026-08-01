from app.core.config import Settings
from app.services.providers.openai_compatible import OpenAICompatibleProvider

_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="openrouter",
            url=_URL,
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENROUTER_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            missing_key_env="OPENROUTER_API_KEY",
        )
