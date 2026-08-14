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

PRODUCTION_APP_ENVS = {"production", "prod"}


def build_provider_chain(settings: Settings) -> ProviderChain:
    is_production = settings.APP_ENV in PRODUCTION_APP_ENVS

    if settings.AI_PROVIDER_MODE == "stub":
        if is_production:
            raise RuntimeError(
                "AI_PROVIDER_MODE must not be 'stub' in production "
                f"(APP_ENV={settings.APP_ENV!r})"
            )
        return ProviderChain([StubProvider()])

    providers: list[AiLookupProvider] = []
    if settings.GEMINI_API_KEY:
        providers.append(GeminiProvider(settings))
    if settings.GROQ_API_KEY:
        providers.append(GroqProvider(settings))
    if settings.OPENROUTER_API_KEY:
        providers.append(OpenRouterProvider(settings))

    if not providers:
        if is_production:
            raise RuntimeError(
                "No AI provider API key configured in production "
                f"(APP_ENV={settings.APP_ENV!r}); "
                "refusing to fall back to the stub provider"
            )
        # No real provider configured (e.g. running tests without keys) -
        # fall back to the stub instead of failing every request.
        providers.append(StubProvider())

    return ProviderChain(providers)


def get_lookup_service(settings: Settings = Depends(get_settings)) -> LookupService:
    return LookupService(build_provider_chain(settings))


def get_translate_service(
    settings: Settings = Depends(get_settings),
) -> TranslateService:
    return TranslateService(build_provider_chain(settings))
