from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FuelType(str, Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    GPL = "gpl"
    HYBRID = "hybrid"


class Locale(str, Enum):
    PT_PT = "pt-PT"
    EN_GB = "en-GB"
    ES_ES = "es-ES"


class LookupRequest(BaseModel):
    brand: str
    model: str
    year: int
    engine: str
    fuelType: FuelType
    doors: int | None = None
    language: Locale = Locale.EN_GB


class AiFixResult(BaseModel):
    summary: str
    steps: str
    estimatedCostEur: float | None = None


class AiKnownIssueResult(BaseModel):
    title: str
    description: str
    severity: IssueSeverity
    typicalKm: int | None = None
    sources: list[str] | None = None
    fixes: list[AiFixResult]


class AiVehicleResult(BaseModel):
    brand: str
    model: str
    name: str = Field(
        description='Commercial name including generation when known, e.g. "Polo 6N1"'
    )
    year: int
    engine: str
    doors: int | None = None
    fuelType: FuelType | None = None
    techSpecs: dict[str, Any] | None = None


class LookupResponse(BaseModel):
    vehicle: AiVehicleResult
    knownIssues: list[AiKnownIssueResult]
