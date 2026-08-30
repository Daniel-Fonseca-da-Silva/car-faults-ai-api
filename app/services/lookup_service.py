from fastapi import HTTPException, status

from app.schemas.lookup import LookupRequest, LookupResponse
from app.services.providers.chain import AllProvidersFailedError, ProviderChain
from app.services.response_safety import sanitize_known_issues
from app.services.retrieval.keyword_retriever import KeywordRetriever


class LookupService:
    def __init__(
        self,
        chain: ProviderChain,
        retriever: KeywordRetriever | None = None,
        *,
        rag_max_chunks: int = 5,
    ) -> None:
        self._chain = chain
        self._retriever = retriever
        self._rag_max_chunks = rag_max_chunks

    async def lookup(self, request: LookupRequest) -> LookupResponse:
        retrieved_chunks = (
            self._retriever.retrieve(request, max_chunks=self._rag_max_chunks)
            if self._retriever is not None
            else []
        )

        try:
            result = await self._chain.generate(request, retrieved_chunks)
        except AllProvidersFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc

        allowed_sources = {
            chunk.sourceUrl for chunk in retrieved_chunks if chunk.sourceUrl
        } or None
        sanitize_known_issues(result.knownIssues, allowed_sources=allowed_sources)
        return result
