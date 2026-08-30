import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.providers.base import AiLookupProvider, ProviderError
from app.services.response_quality import (
    enforce_lookup_quality,
    enforce_translate_quality,
)
from app.services.retrieval.models import KnowledgeChunk

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AllProvidersFailedError(Exception):
    """Raised when every provider in the chain has failed."""


class ProviderChain:
    def __init__(
        self, providers: list[AiLookupProvider], *, log_metrics: bool = True
    ) -> None:
        self._providers = providers
        self._log_metrics = log_metrics

    async def generate(
        self,
        request: LookupRequest,
        retrieved_chunks: list[KnowledgeChunk] | None = None,
    ) -> LookupResponse:
        return await self._run(
            "ai_lookup",
            lambda provider: provider.generate(request, retrieved_chunks),
            enforce_lookup_quality,
        )

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        return await self._run(
            "ai_translate",
            lambda provider: provider.translate(request),
            enforce_translate_quality,
        )

    async def _run(
        self,
        operation: str,
        call: Callable[[AiLookupProvider], Awaitable[T]],
        validate: Callable[[T], None],
    ) -> T:
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                result = await call(provider)
                validate(result)
            except ProviderError as exc:
                logger.warning(
                    "%s_provider_failed provider=%s error=%s",
                    operation,
                    provider.name,
                    exc,
                )
                last_error = exc
                continue

            self._log_success(operation, provider)
            return result
        raise AllProvidersFailedError(
            str(last_error) if last_error else "no AI provider configured"
        )

    def _log_success(self, operation: str, provider: AiLookupProvider) -> None:
        metrics = getattr(provider, "last_metrics", None) if self._log_metrics else None
        if metrics is None:
            logger.info("%s_succeeded provider=%s", operation, provider.name)
            return
        logger.info(
            "%s_succeeded provider=%s latency_ms=%s tokens_in=%s tokens_out=%s",
            operation,
            provider.name,
            metrics.latency_ms,
            metrics.tokens_in,
            metrics.tokens_out,
        )
