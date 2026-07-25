import pytest
from fastapi import HTTPException

from app.api.dependencies import get_lookup_service, get_translate_service
from app.main import app
from app.schemas.lookup import (
    AiKnownIssueResult,
    FuelType,
    IssueSeverity,
    Locale,
    LookupRequest,
)
from app.schemas.translate import TranslateRequest
from app.services.lookup_service import LookupService
from app.services.providers.base import ProviderError
from app.services.providers.chain import AllProvidersFailedError, ProviderChain
from app.services.providers.stub import StubProvider
from app.services.translate_service import TranslateService

REQUEST = LookupRequest(
    brand="Renault", model="Clio", year=2018, engine="1.5 dCi", fuelType=FuelType.DIESEL
)

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


class FailingProvider:
    def __init__(self, name: str):
        self.name = name

    async def generate(self, request):
        raise ProviderError(f"{self.name} failed")

    async def translate(self, request):
        raise ProviderError(f"{self.name} failed")


class WorkingProvider:
    name = "working"

    async def generate(self, request):
        return await StubProvider().generate(request)

    async def translate(self, request):
        return await StubProvider().translate(request)


async def test_chain_fails_over_to_next_provider():
    chain = ProviderChain([FailingProvider("gemini"), WorkingProvider()])

    result = await chain.generate(REQUEST)

    assert result.vehicle.brand == "Renault"


async def test_chain_raises_when_all_providers_fail():
    chain = ProviderChain([FailingProvider("gemini"), FailingProvider("groq")])

    with pytest.raises(AllProvidersFailedError):
        await chain.generate(REQUEST)


async def test_lookup_service_raises_503_when_all_providers_fail():
    chain = ProviderChain([FailingProvider("gemini")])
    service = LookupService(chain)

    with pytest.raises(HTTPException) as exc_info:
        await service.lookup(REQUEST)

    assert exc_info.value.status_code == 503


async def test_lookup_endpoint_returns_503_when_all_providers_fail(
    async_client, auth_headers
):
    failing_chain = ProviderChain([FailingProvider("gemini"), FailingProvider("groq")])
    app.dependency_overrides[get_lookup_service] = lambda: LookupService(failing_chain)
    try:
        response = await async_client.post(
            "/lookup",
            json={
                "brand": "Renault",
                "model": "Clio",
                "year": 2018,
                "engine": "1.5 dCi",
                "fuelType": "diesel",
            },
            headers=auth_headers,
        )
    finally:
        app.dependency_overrides.pop(get_lookup_service, None)

    assert response.status_code == 503


async def test_lookup_endpoint_succeeds_after_failover(async_client, auth_headers):
    mixed_chain = ProviderChain([FailingProvider("gemini"), WorkingProvider()])
    app.dependency_overrides[get_lookup_service] = lambda: LookupService(mixed_chain)
    try:
        response = await async_client.post(
            "/lookup",
            json={
                "brand": "Renault",
                "model": "Clio",
                "year": 2018,
                "engine": "1.5 dCi",
                "fuelType": "diesel",
            },
            headers=auth_headers,
        )
    finally:
        app.dependency_overrides.pop(get_lookup_service, None)

    assert response.status_code == 200
    assert response.json()["vehicle"]["brand"] == "Renault"


async def test_chain_translate_fails_over_to_next_provider():
    chain = ProviderChain([FailingProvider("gemini"), WorkingProvider()])

    result = await chain.translate(TRANSLATE_REQUEST)

    assert result.knownIssues[0].title == "[pt-PT] Gearbox"


async def test_chain_translate_raises_when_all_providers_fail():
    chain = ProviderChain([FailingProvider("gemini"), FailingProvider("groq")])

    with pytest.raises(AllProvidersFailedError):
        await chain.translate(TRANSLATE_REQUEST)


async def test_translate_service_raises_503_when_all_providers_fail():
    chain = ProviderChain([FailingProvider("gemini")])
    service = TranslateService(chain)

    with pytest.raises(HTTPException) as exc_info:
        await service.translate(TRANSLATE_REQUEST)

    assert exc_info.value.status_code == 503


async def test_translate_endpoint_returns_503_when_all_providers_fail(
    async_client, auth_headers
):
    failing_chain = ProviderChain([FailingProvider("gemini"), FailingProvider("groq")])
    app.dependency_overrides[get_translate_service] = lambda: TranslateService(
        failing_chain
    )
    try:
        response = await async_client.post(
            "/translate",
            json={
                "sourceLanguage": "en-GB",
                "targetLanguage": "pt-PT",
                "knownIssues": [
                    {
                        "title": "Gearbox",
                        "description": "Wears out",
                        "severity": "high",
                        "fixes": [],
                    }
                ],
            },
            headers=auth_headers,
        )
    finally:
        app.dependency_overrides.pop(get_translate_service, None)

    assert response.status_code == 503
