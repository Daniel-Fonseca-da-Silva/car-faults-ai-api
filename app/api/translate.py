from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_translate_service
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import verify_api_key
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.translate_service import TranslateService

router = APIRouter(tags=["translate"])


@router.post(
    "/translate",
    response_model=TranslateResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(get_settings().RATE_LIMIT)
async def translate(
    request: Request,
    payload: TranslateRequest,
    service: TranslateService = Depends(get_translate_service),
) -> TranslateResponse:
    return await service.translate(payload)
