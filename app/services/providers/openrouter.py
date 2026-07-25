import httpx

from app.core.config import Settings
from app.prompts.loader import (
    build_translate_user_prompt,
    build_user_prompt,
    load_system_prompt,
    load_translate_system_prompt,
)
from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.providers.base import ProviderError
from app.services.providers.util import extract_json_object

_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider:
    name = "openrouter"

    def __init__(self, settings: Settings):
        self._api_key = settings.OPENROUTER_API_KEY
        self._model = settings.OPENROUTER_MODEL
        self._timeout = settings.AI_TIMEOUT_SECONDS

    async def generate(self, request: LookupRequest) -> LookupResponse:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not configured")

        text = await self._complete(load_system_prompt(), build_user_prompt(request))

        try:
            payload = extract_json_object(text)
            return LookupResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"OpenRouter returned an invalid response: {exc}"
            ) from exc

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not configured")

        text = await self._complete(
            load_translate_system_prompt(), build_translate_user_prompt(request)
        )

        try:
            payload = extract_json_object(text)
            return TranslateResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"OpenRouter returned an invalid response: {exc}"
            ) from exc

    async def _complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    _URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                    },
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc

        if response.status_code != 200:
            raise ProviderError(
                f"OpenRouter responded with status {response.status_code}"
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"OpenRouter returned an invalid response: {exc}"
            ) from exc
