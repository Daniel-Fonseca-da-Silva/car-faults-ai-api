from app.core.config import Settings
from app.services.providers.openai_compatible import OpenAICompatibleProvider

_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="groq",
            url=_URL,
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            missing_key_env="GROQ_API_KEY",
            use_json_response_format=settings.AI_RESPONSE_FORMAT_JSON,
        )
