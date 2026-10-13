import pytest

from app.api.dependencies import build_provider_chain
from app.core.config import get_settings
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.services.providers.mistral import MistralProvider
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
            GEMINI_API_KEY_BACKUP=None,
            GROQ_API_KEY=None,
            OPENROUTER_API_KEY=None,
            MISTRAL_API_KEY=None,
        )
    )

    assert [p.name for p in chain._providers] == ["stub"]


@pytest.mark.parametrize("app_env", ["production", "prod"])
def test_stub_mode_raises_in_production(app_env):
    with pytest.raises(RuntimeError, match="AI_PROVIDER_MODE"):
        build_provider_chain(_settings(APP_ENV=app_env, AI_PROVIDER_MODE="stub"))


@pytest.mark.parametrize("app_env", ["production", "prod"])
def test_chain_mode_without_any_key_raises_in_production(app_env):
    with pytest.raises(RuntimeError, match="No AI provider API key"):
        build_provider_chain(
            _settings(
                APP_ENV=app_env,
                AI_PROVIDER_MODE="chain",
                GEMINI_API_KEY=None,
                GEMINI_API_KEY_BACKUP=None,
                GROQ_API_KEY=None,
                OPENROUTER_API_KEY=None,
                MISTRAL_API_KEY=None,
            )
        )


def test_chain_mode_includes_only_configured_providers():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY="gemini-key",
            GEMINI_API_KEY_BACKUP=None,
            GROQ_API_KEY=None,
            OPENROUTER_API_KEY="or-key",
            MISTRAL_API_KEY=None,
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
            GEMINI_API_KEY_BACKUP=None,
            GROQ_API_KEY="groq-key",
            OPENROUTER_API_KEY="or-key",
            MISTRAL_API_KEY=None,
        )
    )

    providers = chain._providers
    assert isinstance(providers[0], GeminiProvider)
    assert isinstance(providers[1], GroqProvider)
    assert isinstance(providers[2], OpenRouterProvider)


def test_chain_mode_with_backup_key_tries_it_right_after_primary_gemini():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY="gemini-key",
            GEMINI_API_KEY_BACKUP="gemini-backup-key",
            GROQ_API_KEY="groq-key",
            OPENROUTER_API_KEY="or-key",
            MISTRAL_API_KEY=None,
        )
    )

    assert [p.name for p in chain._providers] == [
        "gemini",
        "gemini_backup",
        "groq",
        "openrouter",
    ]
    assert chain._providers[0]._api_key == "gemini-key"
    assert chain._providers[1]._api_key == "gemini-backup-key"


def test_chain_mode_with_only_backup_gemini_key():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY=None,
            GEMINI_API_KEY_BACKUP="gemini-backup-key",
            GROQ_API_KEY=None,
            OPENROUTER_API_KEY=None,
            MISTRAL_API_KEY=None,
        )
    )

    assert [p.name for p in chain._providers] == ["gemini_backup"]


def test_chain_mode_with_every_key_orders_mistral_before_openrouter():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY="gemini-key",
            GEMINI_API_KEY_BACKUP="gemini-backup-key",
            GROQ_API_KEY="groq-key",
            MISTRAL_API_KEY="mistral-key",
            OPENROUTER_API_KEY="or-key",
        )
    )

    assert [p.name for p in chain._providers] == [
        "gemini",
        "gemini_backup",
        "groq",
        "mistral",
        "openrouter",
    ]
    assert isinstance(chain._providers[3], MistralProvider)


def test_chain_mode_with_only_mistral_key():
    chain = build_provider_chain(
        _settings(
            AI_PROVIDER_MODE="chain",
            GEMINI_API_KEY=None,
            GEMINI_API_KEY_BACKUP=None,
            GROQ_API_KEY=None,
            MISTRAL_API_KEY="mistral-key",
            OPENROUTER_API_KEY=None,
        )
    )

    assert [p.name for p in chain._providers] == ["mistral"]


def test_settings_require_model_when_its_api_key_is_set(monkeypatch):
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("MISTRAL_MODEL", "")

    with pytest.raises(ValidationError, match="MISTRAL_MODEL"):
        Settings()


def test_settings_require_gemini_model_for_backup_key(monkeypatch):
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_BACKUP", "gemini-backup-key")
    monkeypatch.setenv("GEMINI_MODEL", "")

    with pytest.raises(ValidationError, match="GEMINI_MODEL"):
        Settings()


def test_settings_allow_missing_model_when_provider_key_is_absent(monkeypatch):
    from app.core.config import Settings

    monkeypatch.setenv("MISTRAL_API_KEY", "")
    monkeypatch.setenv("MISTRAL_MODEL", "")

    assert Settings().MISTRAL_MODEL == ""
