"""Post-LLM output safety checks shared by lookup and translate.

Providers occasionally hallucinate malformed or suspicious values (e.g. a
non-URL string, a non-https scheme, or an IP-literal host) in the `sources`
field. This module filters those out before a response reaches the Nest
caller.
"""

import re
from urllib.parse import urlparse

from app.schemas.lookup import AiKnownIssueResult

_ALLOWED_SCHEME = "https"
_DOMAIN_PATTERN = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


def _is_safe_source_url(source: str) -> bool:
    parsed = urlparse(source)
    hostname = parsed.hostname
    if hostname is None:
        return False
    if parsed.scheme != _ALLOWED_SCHEME:
        return False
    return _DOMAIN_PATTERN.match(hostname) is not None


def sanitize_sources(sources: list[str] | None) -> list[str] | None:
    """Keep only well-formed https:// URLs with a valid domain, else drop them."""
    if sources is None:
        return None

    safe_sources = [source for source in sources if _is_safe_source_url(source)]
    return safe_sources or None


def sanitize_known_issues(
    known_issues: list[AiKnownIssueResult],
) -> list[AiKnownIssueResult]:
    for issue in known_issues:
        issue.sources = sanitize_sources(issue.sources)
    return known_issues
