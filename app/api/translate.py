from fastapi import APIRouter, Depends

from app.api.dependencies import get_translate_service
from app.core.security import verify_api_key
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.translate_service import TranslateService

router = APIRouter(tags=["translate"])


@router.post(
    "/translate",
    response_model=TranslateResponse,
    dependencies=[Depends(verify_api_key)],
)
async def translate(
    request: TranslateRequest,
    service: TranslateService = Depends(get_translate_service),
) -> TranslateResponse:
    return await service.translate(request)
