from typing import cast

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

_settings = get_settings()

# REDIS_URL unset -> in-memory storage (fine for local/dev single-process
# runs). Set it in any multi-instance deployment so the limit is shared
# across processes instead of being tracked per-instance.
limiter = (
    Limiter(key_func=get_remote_address, storage_uri=_settings.REDIS_URL)
    if _settings.REDIS_URL
    else Limiter(key_func=get_remote_address)
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))
