from fastapi import HTTPException, status

from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.providers.chain import AllProvidersFailedError, ProviderChain
from app.services.response_safety import sanitize_known_issues


class TranslateService:
    def __init__(self, chain: ProviderChain) -> None:
        self._chain = chain

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        try:
            result = await self._chain.translate(request)
        except AllProvidersFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc

        sanitize_known_issues(result.knownIssues)
        return result
