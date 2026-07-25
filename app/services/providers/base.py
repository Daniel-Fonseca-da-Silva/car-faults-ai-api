from typing import Protocol

from app.schemas.lookup import LookupRequest, LookupResponse
from app.schemas.translate import TranslateRequest, TranslateResponse


class ProviderError(Exception):
    """Raised when a provider fails to produce a valid lookup result."""


class AiLookupProvider(Protocol):
    name: str

    async def generate(self, request: LookupRequest) -> LookupResponse: ...
    async def translate(self, request: TranslateRequest) -> TranslateResponse: ...
