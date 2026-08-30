"""Post-LLM quality gating shared by lookup and translate, on top of Pydantic.

Pydantic already enforces shape; this module enforces the response is
*useful* - non-empty, bounded, with clean numeric/URL fields - and signals
failover (via ProviderError) only for the case that isn't worth serving at
all: a lookup with zero known issues.
"""

import logging

from app.schemas.lookup import AiKnownIssueResult, IssueSeverity, LookupResponse
from app.schemas.translate import TranslateResponse
from app.services.providers.base import ProviderError
from app.services.response_safety import sanitize_sources

logger = logging.getLogger(__name__)

MAX_KNOWN_ISSUES = 15
_MIN_TYPICAL_KM = 0
_MAX_TYPICAL_KM = 500_000

# Coarse keyword heuristics for the severity/text consistency check below -
# not a classifier, just enough signal to log a warning worth a human look.
_HIGH_SEVERITY_SIGNALS = (
    "brake",
    "travão",
    "freio",
    "airbag",
    "fire",
    "incêndio",
    "fogo",
    "steering",
    "direção",
    "immobiliz",
    "imobiliz",
    "safety recall",
    "recall de segurança",
    "seizure",
    "gripagem",
)
_LOW_SEVERITY_SIGNALS = (
    "cosmetic",
    "estético",
    "rattle",
    "chocalho",
    "trim",
    "acabamento",
    "minor noise",
    "ruído ligeiro",
)


def _warn_if_severity_inconsistent(issue: AiKnownIssueResult) -> None:
    text = f"{issue.title} {issue.description}".lower()
    has_high_signal = any(signal in text for signal in _HIGH_SEVERITY_SIGNALS)
    has_low_signal = any(signal in text for signal in _LOW_SEVERITY_SIGNALS)

    if issue.severity in (IssueSeverity.LOW, IssueSeverity.MEDIUM) and has_high_signal:
        logger.warning(
            "ai_quality_severity_mismatch severity=%s title=%r reason=high_signal_text",
            issue.severity.value,
            issue.title,
        )
    elif (
        issue.severity in (IssueSeverity.HIGH, IssueSeverity.CRITICAL)
        and has_low_signal
        and not has_high_signal
    ):
        logger.warning(
            "ai_quality_severity_mismatch severity=%s title=%r reason=low_signal_text",
            issue.severity.value,
            issue.title,
        )


def _sanitize_issue(issue: AiKnownIssueResult) -> None:
    if issue.typicalKm is not None and not (
        _MIN_TYPICAL_KM <= issue.typicalKm <= _MAX_TYPICAL_KM
    ):
        issue.typicalKm = None
    issue.sources = sanitize_sources(issue.sources)
    _warn_if_severity_inconsistent(issue)


def enforce_lookup_quality(response: LookupResponse) -> None:
    """Mutate `response` in place; raise ProviderError if it's unusable."""
    if not response.knownIssues:
        raise ProviderError("response has no known issues")
    if len(response.knownIssues) > MAX_KNOWN_ISSUES:
        response.knownIssues = response.knownIssues[:MAX_KNOWN_ISSUES]
    for issue in response.knownIssues:
        _sanitize_issue(issue)


def enforce_translate_quality(response: TranslateResponse) -> None:
    """Mutate `response` in place - same per-issue rules, no emptiness gate."""
    for issue in response.knownIssues:
        _sanitize_issue(issue)
