import time
from typing import cast

import httpx

from app.prompts.loader import (
    build_translate_user_prompt,
    build_user_prompt,
    load_system_prompt,
    load_translate_system_prompt,
)
from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.ai_metrics import AiCallMetrics
from app.services.providers.base import ProviderError
from app.services.providers.retry import post_with_retry
from app.services.providers.util import extract_json_object
from app.services.retrieval.models import KnowledgeChunk


class OpenAICompatibleProvider:
    """Base for providers exposing an OpenAI-compatible chat-completions API."""

    def __init__(
        self,
        *,
        name: str,
        url: str,
        api_key: str | None,
        model: str,
        timeout: float,
        missing_key_env: str,
        use_json_response_format: bool = True,
    ) -> None:
        self.name = name
        self._url = url
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._missing_key_env = missing_key_env
        self._use_json_response_format = use_json_response_format
        self._last_metrics: AiCallMetrics | None = None

    @property
    def last_metrics(self) -> AiCallMetrics | None:
        return self._last_metrics

    async def generate(
        self,
        request: LookupRequest,
        retrieved_chunks: list[KnowledgeChunk] | None = None,
    ) -> LookupResponse:
        self._require_api_key()

        user_prompt = build_user_prompt(request, retrieved_chunks=retrieved_chunks)
        text = await self._complete(load_system_prompt(), user_prompt)

        try:
            payload = extract_json_object(text)
            return LookupResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"{self.name} returned an invalid response: {exc}"
            ) from exc

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        self._require_api_key()

        text = await self._complete(
            load_translate_system_prompt(), build_translate_user_prompt(request)
        )

        try:
            payload = extract_json_object(text)
            return TranslateResponse(**payload)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"{self.name} returned an invalid response: {exc}"
            ) from exc

    def _require_api_key(self) -> None:
        if not self._api_key:
            raise ProviderError(f"{self._missing_key_env} is not configured")

    async def _complete(self, system_prompt: str, user_prompt: str) -> str:
        started = time.perf_counter()
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if self._use_json_response_format:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await post_with_retry(
                    client,
                    self._url,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} request failed: {exc}") from exc

        if response.status_code != 200:
            body = response.text.strip()
            detail = f": {body}" if body else ""
            raise ProviderError(
                f"{self.name} responded with status {response.status_code}{detail}"
            )

        try:
            data = response.json()
            content = cast(str, data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ProviderError(
                f"{self.name} returned an invalid response: {exc}"
            ) from exc

        usage = data.get("usage") or {}
        self._last_metrics = AiCallMetrics(
            provider=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
        )
        return content
