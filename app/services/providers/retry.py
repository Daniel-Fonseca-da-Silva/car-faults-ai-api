import asyncio
from collections.abc import Mapping

import httpx

# 429 (rate limited) and the common transient-gateway 5xx codes - worth a
# short retry before failing over to the next provider in the chain.
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
MAX_RETRIES = 2
BACKOFF_SECONDS = [1.0, 2.0]


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
    """
    attempt = 0
    while True:
        response = await client.post(url, headers=headers, json=json)
        if response.status_code not in RETRYABLE_STATUS_CODES or attempt >= MAX_RETRIES:
            return response
        await asyncio.sleep(BACKOFF_SECONDS[attempt])
        attempt += 1
