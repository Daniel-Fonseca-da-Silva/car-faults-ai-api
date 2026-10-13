from app.core.config import Settings
from app.services.providers.openai_compatible import OpenAICompatibleProvider

_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="mistral",
            url=_URL,
            api_key=settings.MISTRAL_API_KEY,
            model=settings.MISTRAL_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            missing_key_env="MISTRAL_API_KEY",
            missing_model_env="MISTRAL_MODEL",
            use_json_response_format=settings.AI_RESPONSE_FORMAT_JSON,
        )
