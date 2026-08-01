from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.lookup_service import LookupService
from app.services.providers.base import AiLookupProvider
from app.services.providers.chain import ProviderChain
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.services.providers.openrouter import OpenRouterProvider
from app.services.providers.stub import StubProvider
from app.services.translate_service import TranslateService


def build_provider_chain(settings: Settings) -> ProviderChain:
    if settings.AI_PROVIDER_MODE == "stub":
        return ProviderChain([StubProvider()])

    providers: list[AiLookupProvider] = []
    if settings.GEMINI_API_KEY:
        providers.append(GeminiProvider(settings))
    if settings.GROQ_API_KEY:
        providers.append(GroqProvider(settings))
    if settings.OPENROUTER_API_KEY:
        providers.append(OpenRouterProvider(settings))

    if not providers:
        # No real provider configured (e.g. running tests without keys) —
        # fall back to the stub instead of failing every request.
        providers.append(StubProvider())

    return ProviderChain(providers)


def get_lookup_service(settings: Settings = Depends(get_settings)) -> LookupService:
    return LookupService(build_provider_chain(settings))


def get_translate_service(
    settings: Settings = Depends(get_settings),
) -> TranslateService:
    return TranslateService(build_provider_chain(settings))
