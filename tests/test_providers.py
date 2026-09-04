from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.config import get_settings
from app.schemas.lookup import (
    AiKnownIssueResult,
    FuelType,
    IssueSeverity,
    Locale,
    LookupRequest,
)
from app.schemas.translate import TranslateRequest
from app.services.providers.base import ProviderError
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.services.providers.openai_compatible import OpenAICompatibleProvider
from app.services.providers.openrouter import OpenRouterProvider

REQUEST = LookupRequest(
    brand="Volkswagen",
    model="Polo",
    year=2015,
    engine="1.2 TSI",
    fuelType=FuelType.GASOLINE,
    doors=5,
)

VALID_RESULT = {
    "vehicle": {
        "brand": "Volkswagen",
        "model": "Polo",
        "name": "Polo 6C",
        "year": 2015,
        "engine": "1.2 TSI",
    },
    "knownIssues": [
        {
            "title": "Issue",
            "description": "Desc",
            "severity": "low",
            "fixes": [{"summary": "Fix", "steps": "Steps"}],
        }
    ],
}

TRANSLATE_REQUEST = TranslateRequest(
    sourceLanguage=Locale.EN_GB,
    targetLanguage=Locale.PT_PT,
    knownIssues=[
        AiKnownIssueResult(
            title="Gearbox",
            description="Wears out",
            severity=IssueSeverity.HIGH,
            fixes=[],
        )
    ],
)

VALID_TRANSLATE_RESULT = {
    "knownIssues": [
        {
            "title": "Caixa de velocidades",
            "description": "Desgasta-se",
            "severity": "high",
            "fixes": [],
        }
    ],
}


class FakeResponse:
    def __init__(self, status_code: int, json_data=None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def _settings(**overrides):
    settings = get_settings()
    return settings.model_copy(update=overrides)


# --- Gemini -----------------------------------------------------------------


async def test_gemini_missing_api_key_raises():
    provider = GeminiProvider(_settings(GEMINI_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.generate(REQUEST)


async def test_gemini_success_parses_response():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": __import__("json").dumps(VALID_RESULT)}]
                    }
                }
            ]
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.generate(REQUEST)

    assert result.vehicle.brand == "Volkswagen"
    assert result.knownIssues[0].title == "Issue"


async def test_gemini_sends_api_key_as_header_not_query_param():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": __import__("json").dumps(VALID_RESULT)}]
                    }
                }
            ]
        },
    )
    mock_post = AsyncMock(return_value=fake)

    with patch("httpx.AsyncClient.post", new=mock_post):
        await provider.generate(REQUEST)

    _, kwargs = mock_post.call_args
    assert kwargs.get("headers", {}).get("x-goog-api-key") == "key"
    assert "params" not in kwargs


async def test_gemini_non_200_raises():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(500, {})

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_gemini_malformed_payload_raises():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(200, {"candidates": []})

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_gemini_network_error_raises():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))

    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(side_effect=httpx.ConnectError("boom")),
    ):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_gemini_translate_missing_api_key_raises():
    provider = GeminiProvider(_settings(GEMINI_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.translate(TRANSLATE_REQUEST)


async def test_gemini_translate_success_parses_response():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": __import__("json").dumps(VALID_TRANSLATE_RESULT)}
                        ]
                    }
                }
            ]
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.translate(TRANSLATE_REQUEST)

    assert result.knownIssues[0].title == "Caixa de velocidades"


# --- Groq ---------------------------------------------------------------


async def test_groq_missing_api_key_raises():
    provider = GroqProvider(_settings(GROQ_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.generate(REQUEST)


async def test_groq_success_parses_response():
    provider = GroqProvider(_settings(GROQ_API_KEY="key"))
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(VALID_RESULT)}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.generate(REQUEST)

    assert result.vehicle.model == "Polo"


async def test_groq_non_200_raises():
    provider = GroqProvider(_settings(GROQ_API_KEY="key"))
    fake = FakeResponse(429, {})

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_groq_translate_missing_api_key_raises():
    provider = GroqProvider(_settings(GROQ_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.translate(TRANSLATE_REQUEST)


async def test_groq_translate_success_parses_response():
    provider = GroqProvider(_settings(GROQ_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "choices": [
                {
                    "message": {
                        "content": __import__("json").dumps(VALID_TRANSLATE_RESULT)
                    }
                }
            ]
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.translate(TRANSLATE_REQUEST)

    assert result.knownIssues[0].title == "Caixa de velocidades"


async def test_groq_extra_top_level_field_in_response_raises():
    provider = GroqProvider(_settings(GROQ_API_KEY="key"))
    payload = {**VALID_RESULT, "evil": True}
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(payload)}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_groq_extra_field_in_vehicle_raises():
    provider = GroqProvider(_settings(GROQ_API_KEY="key"))
    payload = {
        **VALID_RESULT,
        "vehicle": {**VALID_RESULT["vehicle"], "evil": "smuggled"},
    }
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(payload)}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


# --- OpenRouter -----------------------------------------------------------


async def test_openrouter_missing_api_key_raises():
    provider = OpenRouterProvider(_settings(OPENROUTER_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.generate(REQUEST)


async def test_openrouter_success_parses_response():
    provider = OpenRouterProvider(_settings(OPENROUTER_API_KEY="key"))
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(VALID_RESULT)}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.generate(REQUEST)

    assert result.vehicle.engine == "1.2 TSI"


async def test_openrouter_invalid_json_raises():
    provider = OpenRouterProvider(_settings(OPENROUTER_API_KEY="key"))
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": "not json"}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_openrouter_translate_missing_api_key_raises():
    provider = OpenRouterProvider(_settings(OPENROUTER_API_KEY=None))

    with pytest.raises(ProviderError):
        await provider.translate(TRANSLATE_REQUEST)


async def test_openrouter_translate_success_parses_response():
    provider = OpenRouterProvider(_settings(OPENROUTER_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "choices": [
                {
                    "message": {
                        "content": __import__("json").dumps(VALID_TRANSLATE_RESULT)
                    }
                }
            ]
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.translate(TRANSLATE_REQUEST)

    assert result.knownIssues[0].title == "Caixa de velocidades"


# --- OpenAICompatibleProvider (shared base) --------------------------------


def _openai_compatible_provider(
    api_key: str | None = "key",
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        name="custom",
        url="https://example.test/v1/chat/completions",
        api_key=api_key,
        model="model-x",
        timeout=5.0,
        missing_key_env="CUSTOM_API_KEY",
    )


async def test_openai_compatible_missing_api_key_raises():
    provider = _openai_compatible_provider(api_key=None)

    with pytest.raises(ProviderError, match="CUSTOM_API_KEY"):
        await provider.generate(REQUEST)


async def test_openai_compatible_success_parses_response():
    provider = _openai_compatible_provider()
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(VALID_RESULT)}}]},
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await provider.generate(REQUEST)

    assert result.vehicle.brand == "Volkswagen"


async def test_openai_compatible_non_200_raises():
    provider = _openai_compatible_provider()
    fake = FakeResponse(500, {})

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)


async def test_groq_and_openrouter_share_openai_compatible_base():
    assert issubclass(GroqProvider, OpenAICompatibleProvider)
    assert issubclass(OpenRouterProvider, OpenAICompatibleProvider)


# --- JSON mode --------------------------------------------------------------


async def test_openai_compatible_requests_json_object_mode():
    provider = _openai_compatible_provider()
    fake = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(VALID_RESULT)}}]},
    )
    mock_post = AsyncMock(return_value=fake)

    with patch("httpx.AsyncClient.post", new=mock_post):
        await provider.generate(REQUEST)

    _, kwargs = mock_post.call_args
    assert kwargs["json"]["response_format"] == {"type": "json_object"}


async def test_gemini_requests_json_mime_type_without_response_schema():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": __import__("json").dumps(VALID_RESULT)}]
                    }
                }
            ]
        },
    )
    mock_post = AsyncMock(return_value=fake)

    with patch("httpx.AsyncClient.post", new=mock_post):
        await provider.generate(REQUEST)

    _, kwargs = mock_post.call_args
    generation_config = kwargs["json"]["generationConfig"]
    assert generation_config["responseMimeType"] == "application/json"
    assert "responseSchema" not in generation_config
    assert "systemInstruction" in kwargs["json"]
    assert "contents" in kwargs["json"]


# --- Metrics ------------------------------------------------------------


async def test_openai_compatible_records_metrics_on_success():
    provider = _openai_compatible_provider()
    fake = FakeResponse(
        200,
        {
            "choices": [
                {"message": {"content": __import__("json").dumps(VALID_RESULT)}}
            ],
            "usage": {"prompt_tokens": 800, "completion_tokens": 1200},
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        await provider.generate(REQUEST)

    assert provider.last_metrics is not None
    assert provider.last_metrics.provider == "custom"
    assert provider.last_metrics.tokens_in == 800
    assert provider.last_metrics.tokens_out == 1200


async def test_gemini_records_metrics_on_success():
    provider = GeminiProvider(_settings(GEMINI_API_KEY="key"))
    fake = FakeResponse(
        200,
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": __import__("json").dumps(VALID_RESULT)}]
                    }
                }
            ],
            "usageMetadata": {"promptTokenCount": 500, "candidatesTokenCount": 300},
        },
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        await provider.generate(REQUEST)

    assert provider.last_metrics is not None
    assert provider.last_metrics.tokens_in == 500
    assert provider.last_metrics.tokens_out == 300


# --- Retry with backoff ------------------------------------------------------


async def test_openai_compatible_retries_on_429_then_succeeds():
    provider = _openai_compatible_provider()
    success = FakeResponse(
        200,
        {"choices": [{"message": {"content": __import__("json").dumps(VALID_RESULT)}}]},
    )
    rate_limited = FakeResponse(429, {})
    mock_post = AsyncMock(side_effect=[rate_limited, rate_limited, success])

    with (
        patch("httpx.AsyncClient.post", new=mock_post),
        patch("app.services.providers.retry.asyncio.sleep", new=AsyncMock()),
    ):
        result = await provider.generate(REQUEST)

    assert result.vehicle.brand == "Volkswagen"
    assert mock_post.call_count == 3


async def test_openai_compatible_gives_up_after_max_retries():
    provider = _openai_compatible_provider()
    rate_limited = FakeResponse(429, {})
    mock_post = AsyncMock(return_value=rate_limited)

    with (
        patch("httpx.AsyncClient.post", new=mock_post),
        patch("app.services.providers.retry.asyncio.sleep", new=AsyncMock()),
    ):
        with pytest.raises(ProviderError):
            await provider.generate(REQUEST)

    assert mock_post.call_count == 3
