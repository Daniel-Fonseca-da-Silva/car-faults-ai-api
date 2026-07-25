from fastapi import APIRouter, Depends

from app.api.dependencies import get_lookup_service
from app.core.security import verify_api_key
from app.schemas.lookup import LookupRequest, LookupResponse
from app.services.lookup_service import LookupService

router = APIRouter(tags=["lookup"])


@router.post(
    "/lookup",
    response_model=LookupResponse,
    dependencies=[Depends(verify_api_key)],
)
async def lookup(
    request: LookupRequest,
    service: LookupService = Depends(get_lookup_service),
) -> LookupResponse:
    return await service.lookup(request)
