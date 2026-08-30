import time
from typing import cast

import httpx

from app.core.config import Settings
from app.prompts.loader import (
    build_translate_user_prompt,
    build_user_prompt,
    load_system_prompt,
    load_translate_system_prompt,
)
from app.schemas.json_schemas import (
    lookup_response_json_schema,
    translate_response_json_schema,
)
from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.ai_metrics import AiCallMetrics
from app.services.providers.base import ProviderError
from app.services.providers.retry import post_with_retry
from app.services.providers.util import extract_json_object
from app.services.retrieval.models import KnowledgeChunk

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider:
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL
        self._timeout = settings.AI_TIMEOUT_SECONDS
        self._last_metrics: AiCallMetrics | None = None

    @property
    def last_metrics(self) -> AiCallMetrics | None:
        return self._last_metrics

    async def generate(
        self,
        request: LookupRequest,
        retrieved_chunks: list[KnowledgeChunk] | None = None,
    ) -> LookupResponse:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")

        user_prompt = build_user_prompt(request, retrieved_chunks=retrieved_chunks)
        text = await self._generate_content(
            load_system_prompt(), user_prompt, lookup_response_json_schema()
        )

        try:
            payload = extract_json_object(text)
            return LookupResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")

        user_prompt = build_translate_user_prompt(request)
        text = await self._generate_content(
            load_translate_system_prompt(),
            user_prompt,
            translate_response_json_schema(),
        )

        try:
            payload = extract_json_object(text)
            return TranslateResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc

    async def _generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await post_with_retry(
                    client,
                    _URL.format(model=self._model),
                    headers={"x-goog-api-key": cast(str, self._api_key)},
                    json={
                        "systemInstruction": {"parts": [{"text": system_prompt}]},
                        "contents": [{"parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.2,
                            "responseMimeType": "application/json",
                            "responseSchema": response_schema,
                        },
                    },
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        if response.status_code != 200:
            raise ProviderError(f"Gemini responded with status {response.status_code}")

        try:
            data = response.json()
            text = cast(str, data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(f"Gemini returned an invalid response: {exc}") from exc

        usage = data.get("usageMetadata") or {}
        self._last_metrics = AiCallMetrics(
            provider=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
            tokens_in=usage.get("promptTokenCount"),
            tokens_out=usage.get("candidatesTokenCount"),
        )
        return text
