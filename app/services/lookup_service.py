from fastapi import HTTPException, status

from app.schemas.lookup import LookupRequest, LookupResponse
from app.services.providers.chain import AllProvidersFailedError, ProviderChain


def _normalize_tech_specs(response: LookupResponse) -> None:
    """Rename a provider's stray "hp" key to the canonical "power_hp"."""
    tech_specs = response.vehicle.techSpecs
    if tech_specs and "hp" in tech_specs and "power_hp" not in tech_specs:
        tech_specs["power_hp"] = tech_specs.pop("hp")


class LookupService:
    def __init__(self, chain: ProviderChain):
        self._chain = chain

    async def lookup(self, request: LookupRequest) -> LookupResponse:
        try:
            response = await self._chain.generate(request)
        except AllProvidersFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI provider unavailable",
            ) from exc

        _normalize_tech_specs(response)
        return response
