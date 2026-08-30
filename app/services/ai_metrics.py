from dataclasses import dataclass


@dataclass(frozen=True)
class AiCallMetrics:
    """Per-call metrics a provider records for its last successful request."""

    provider: str
    latency_ms: int
    tokens_in: int | None = None
    tokens_out: int | None = None
