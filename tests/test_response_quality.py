import pytest

from app.schemas.lookup import (
    AiFixResult,
    AiKnownIssueResult,
    AiVehicleResult,
    IssueSeverity,
    LookupResponse,
)
from app.schemas.translate import TranslateResponse
from app.services.providers.base import ProviderError
from app.services.response_quality import (
    MAX_KNOWN_ISSUES,
    enforce_lookup_quality,
    enforce_translate_quality,
)

VEHICLE = AiVehicleResult(
    brand="Volkswagen", model="Polo", name="Polo 6C", year=2015, engine="1.2 TSI"
)


def _issue(**overrides) -> AiKnownIssueResult:
    defaults = dict(
        title="Issue",
        description="Desc",
        severity=IssueSeverity.LOW,
        fixes=[AiFixResult(summary="Fix", steps="Steps")],
    )
    defaults.update(overrides)
    return AiKnownIssueResult(**defaults)


def test_enforce_lookup_quality_raises_on_empty_known_issues():
    response = LookupResponse(vehicle=VEHICLE, knownIssues=[])

    with pytest.raises(ProviderError):
        enforce_lookup_quality(response)


def test_enforce_lookup_quality_truncates_beyond_max():
    response = LookupResponse(
        vehicle=VEHICLE, knownIssues=[_issue() for _ in range(MAX_KNOWN_ISSUES + 5)]
    )

    enforce_lookup_quality(response)

    assert len(response.knownIssues) == MAX_KNOWN_ISSUES


@pytest.mark.parametrize("typical_km", [-1, 500_001])
def test_enforce_lookup_quality_nulls_out_of_range_typical_km(typical_km):
    response = LookupResponse(
        vehicle=VEHICLE, knownIssues=[_issue(typicalKm=typical_km)]
    )

    enforce_lookup_quality(response)

    assert response.knownIssues[0].typicalKm is None


def test_enforce_lookup_quality_keeps_in_range_typical_km():
    response = LookupResponse(vehicle=VEHICLE, knownIssues=[_issue(typicalKm=120_000)])

    enforce_lookup_quality(response)

    assert response.knownIssues[0].typicalKm == 120_000


def test_enforce_lookup_quality_filters_non_https_sources():
    response = LookupResponse(
        vehicle=VEHICLE,
        knownIssues=[
            _issue(sources=["http://insecure.example.com", "https://forum.example.com"])
        ],
    )

    enforce_lookup_quality(response)

    assert response.knownIssues[0].sources == ["https://forum.example.com"]


def test_enforce_lookup_quality_logs_warning_on_severity_mismatch(caplog):
    response = LookupResponse(
        vehicle=VEHICLE,
        knownIssues=[
            _issue(
                title="Brake failure",
                description="Complete brake failure risk while driving",
                severity=IssueSeverity.LOW,
            )
        ],
    )

    with caplog.at_level("WARNING"):
        enforce_lookup_quality(response)

    assert "ai_quality_severity_mismatch" in caplog.text


def test_enforce_translate_quality_does_not_raise_on_empty_known_issues():
    response = TranslateResponse(knownIssues=[])

    enforce_translate_quality(response)

    assert response.knownIssues == []


def test_enforce_translate_quality_filters_non_https_sources():
    response = TranslateResponse(
        knownIssues=[_issue(sources=["ftp://example.com", "https://example.com"])]
    )

    enforce_translate_quality(response)

    assert response.knownIssues[0].sources == ["https://example.com"]
