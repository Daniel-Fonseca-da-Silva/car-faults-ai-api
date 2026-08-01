import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.providers.base import AiLookupProvider, ProviderError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AllProvidersFailedError(Exception):
    """Raised when every provider in the chain has failed."""


class ProviderChain:
    def __init__(self, providers: list[AiLookupProvider]) -> None:
        self._providers = providers

    async def generate(self, request: LookupRequest) -> LookupResponse:
        return await self._run("ai_lookup", lambda provider: provider.generate(request))

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        return await self._run(
            "ai_translate", lambda provider: provider.translate(request)
        )

    async def _run(
        self,
        operation: str,
        call: Callable[[AiLookupProvider], Awaitable[T]],
    ) -> T:
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                result = await call(provider)
                logger.info("%s_succeeded provider=%s", operation, provider.name)
                return result
            except ProviderError as exc:
                logger.warning(
                    "%s_provider_failed provider=%s error=%s",
                    operation,
                    provider.name,
                    exc,
                )
                last_error = exc
        raise AllProvidersFailedError(
            str(last_error) if last_error else "no AI provider configured"
        )
