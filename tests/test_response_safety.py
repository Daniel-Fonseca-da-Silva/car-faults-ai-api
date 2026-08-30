from app.schemas.lookup import AiFixResult, AiKnownIssueResult, IssueSeverity
from app.services.response_safety import sanitize_known_issues, sanitize_sources


def test_sanitize_sources_with_none_returns_none():
    assert sanitize_sources(None) is None


def test_sanitize_sources_keeps_valid_https_urls():
    sources = ["https://www.example.com/article", "https://sub.example.co.uk/x"]

    assert sanitize_sources(sources) == sources


def test_sanitize_sources_drops_non_https_scheme():
    assert sanitize_sources(["http://example.com/article"]) is None


def test_sanitize_sources_drops_non_url_text():
    assert sanitize_sources(["VW owner forums"]) is None


def test_sanitize_sources_drops_javascript_scheme():
    assert sanitize_sources(['javascript:alert("x")']) is None


def test_sanitize_sources_filters_mixed_list_keeping_only_safe_entries():
    sources = ["https://example.com/a", "ftp://example.com/b", "not a url"]

    assert sanitize_sources(sources) == ["https://example.com/a"]


def _known_issue(sources: list[str] | None) -> AiKnownIssueResult:
    return AiKnownIssueResult(
        title="Issue",
        description="Description.",
        severity=IssueSeverity.LOW,
        sources=sources,
        fixes=[AiFixResult(summary="Fix", steps="Steps.")],
    )


def test_sanitize_known_issues_mutates_sources_in_place():
    issue = _known_issue(["not a url"])

    result = sanitize_known_issues([issue])

    assert result[0].sources is None
    assert issue.sources is None


def test_sanitize_known_issues_keeps_valid_sources():
    issue = _known_issue(["https://example.com/a"])

    sanitize_known_issues([issue])

    assert issue.sources == ["https://example.com/a"]
