import asyncio
from collections.abc import Mapping

import httpx

# 429 (rate limited) and the common transient-gateway 5xx codes - worth a
# short retry before failing over to the next provider in the chain.
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
MAX_RETRIES = 2
BACKOFF_SECONDS = [1.0, 2.0]

# Markers in a 429 body meaning the quota is used up (Gemini
# RESOURCE_EXHAUSTED, OpenRouter "free-models-per-day") - retrying a few
# seconds later won't help, so fail over to the next provider right away.
QUOTA_EXHAUSTED_MARKERS = ("resource_exhausted", "quota", "per-day", "perday")


def is_quota_exhausted(response: httpx.Response) -> bool:
    if response.status_code != 429:
        return False
    try:
        body = response.text.lower()
    except Exception:
        return False
    return any(marker in body for marker in QUOTA_EXHAUSTED_MARKERS)


async def post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    json: Mapping[str, object] | None = None,
) -> httpx.Response:
    """POST with a short backoff retry on 429/502/503/504.

    Absorbs a transient rate-limit or gateway blip so the ProviderChain
    doesn't fail over to the next provider on every one - callers still get
    the last response back to raise/handle as usual once retries run out.
    A 429 that reports an exhausted quota is returned immediately instead.
    """
    attempt = 0
    while True:
        response = await client.post(url, headers=headers, json=json)
        if (
            response.status_code not in RETRYABLE_STATUS_CODES
            or attempt >= MAX_RETRIES
            or is_quota_exhausted(response)
        ):
            return response
        await asyncio.sleep(BACKOFF_SECONDS[attempt])
        attempt += 1
