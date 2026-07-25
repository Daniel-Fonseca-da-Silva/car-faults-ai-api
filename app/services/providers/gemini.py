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

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider:
    name = "gemini"

    def __init__(self, settings: Settings):
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL
        self._timeout = settings.AI_TIMEOUT_SECONDS

    async def generate(self, request: LookupRequest) -> LookupResponse:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")

        prompt = f"{load_system_prompt()}\n\n{build_user_prompt(request)}"
        text = await self._generate_content(prompt)

        try:
            payload = extract_json_object(text)
            return LookupResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")

        system_prompt = load_translate_system_prompt()
        user_prompt = build_translate_user_prompt(request)
        prompt = f"{system_prompt}\n\n{user_prompt}"
        text = await self._generate_content(prompt)

        try:
            payload = extract_json_object(text)
            return TranslateResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc

    async def _generate_content(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    _URL.format(model=self._model),
                    params={"key": self._api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        if response.status_code != 200:
            raise ProviderError(f"Gemini responded with status {response.status_code}")

        try:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc
