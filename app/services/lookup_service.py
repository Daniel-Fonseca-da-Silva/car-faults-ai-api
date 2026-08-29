from fastapi import HTTPException, status

from app.schemas.lookup import LookupRequest, LookupResponse
from app.services.providers.chain import AllProvidersFailedError, ProviderChain
from app.services.response_safety import sanitize_known_issues


class LookupService:
    def __init__(self, chain: ProviderChain) -> None:
        self._chain = chain

    async def lookup(self, request: LookupRequest) -> LookupResponse:
        try:
            result = await self._chain.generate(request)
        except AllProvidersFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc

        sanitize_known_issues(result.knownIssues)
        return result
