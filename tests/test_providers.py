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
