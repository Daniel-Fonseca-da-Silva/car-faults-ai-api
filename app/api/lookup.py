from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_lookup_service
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import verify_api_key
from app.schemas.lookup import LookupRequest, LookupResponse
from app.services.lookup_service import LookupService

router = APIRouter(tags=["lookup"])


@router.post(
    "/lookup",
    response_model=LookupResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(get_settings().RATE_LIMIT)
async def lookup(
    request: Request,
    payload: LookupRequest,
    service: LookupService = Depends(get_lookup_service),
) -> LookupResponse:
    return await service.lookup(payload)
