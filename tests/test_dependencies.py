from app.api.dependencies import build_provider_chain
from app.core.config import get_settings
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.services.providers.openrouter import OpenRouterProvider


def _settings(**overrides):
    return get_settings().model_copy(update=overrides)


def test_stub_mode_uses_only_stub_provider():
    chain = build_provider_chain(_settings(AI_PROVIDER_MODE="stub"))

    assert [p.name for p in chain._providers] == ["stub"]


def test_chain_mode_without_any_key_falls_back_to_stub():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY=None,
            GROQ_API_KEY=None,
            OPENROUTER_API_KEY=None,
        )
    )

    assert [p.name for p in chain._providers] == ["stub"]


def test_chain_mode_includes_only_configured_providers():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY="gemini-key",
            GROQ_API_KEY=None,
            OPENROUTER_API_KEY="or-key",
        )
    )

    providers = chain._providers
    assert isinstance(providers[0], GeminiProvider)
    assert isinstance(providers[1], OpenRouterProvider)
    assert len(providers) == 2


def test_chain_mode_with_all_keys_orders_gemini_groq_openrouter():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY="gemini-key",
            GROQ_API_KEY="groq-key",
            OPENROUTER_API_KEY="or-key",
        )
    )

    providers = chain._providers
    assert isinstance(providers[0], GeminiProvider)
    assert isinstance(providers[1], GroqProvider)
    assert isinstance(providers[2], OpenRouterProvider)
