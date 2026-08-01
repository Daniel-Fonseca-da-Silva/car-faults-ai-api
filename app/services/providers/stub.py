from app.schemas.lookup import (
    AiFixResult,
    AiKnownIssueResult,
    AiVehicleResult,
    IssueSeverity,
    LookupRequest,
    LookupResponse,
    TechSpecs,
)
from app.schemas.translate import TranslateRequest, TranslateResponse


class StubProvider:
    """Deterministic provider used when no real AI provider is configured."""

    name = "stub"

    async def generate(self, request: LookupRequest) -> LookupResponse:
        return LookupResponse(
            vehicle=AiVehicleResult(
                brand=request.brand,
                model=request.model,
                name=f"{request.brand} {request.model}",
                year=request.year,
                engine=request.engine,
                fuelType=request.fuelType,
                doors=request.doors,
                techSpecs=TechSpecs(power_hp=90),
            ),
            knownIssues=[
                AiKnownIssueResult(
                    title="Stub known issue",
                    description="Placeholder issue returned by the stub AI provider.",
                    severity=IssueSeverity.MEDIUM,
                    fixes=[
                        AiFixResult(
                            summary="Stub fix",
                            steps="Placeholder steps returned by the stub AI provider.",
                        )
                    ],
                )
            ],
        )

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        prefix = f"[{request.targetLanguage.value}] "
        return TranslateResponse(
            knownIssues=[
                AiKnownIssueResult(
                    title=f"{prefix}{issue.title}",
                    description=f"{prefix}{issue.description}",
                    severity=issue.severity,
                    typicalKm=issue.typicalKm,
                    sources=issue.sources,
                    fixes=[
                        AiFixResult(
                            summary=f"{prefix}{fix.summary}",
                            steps=f"{prefix}{fix.steps}",
                            estimatedCostEur=fix.estimatedCostEur,
                        )
                        for fix in issue.fixes
                    ],
                )
                for issue in request.knownIssues
            ]
        )
