from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Vehicle input fields: letters (incl. common European accents), digits,
# spaces and automotive punctuation only - rejects control chars/newlines
# that could be used to smuggle instructions into the LLM prompt.
_VEHICLE_FIELD_MAX_LENGTH = 64
_VEHICLE_FIELD_PATTERN = r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 .\-/()+]+$"

# Free-text fields (titles, descriptions, summaries, steps): same idea as
# VehicleField but with common prose punctuation allowed, including the
# "[pt-PT] " style locale-tag prefix used by the translate stub/providers.
# The allow-list excludes "<", ">", "&", quotes and control chars by
# construction, so it also rejects control-char and basic HTML/script
# injection attempts without needing separate denylist checks.
_SAFE_TEXT_PATTERN = r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 .\-/()+,\n!?;:\[\]]+$"

_NAME_MAX_LENGTH = 200
_TITLE_MAX_LENGTH = 200
_DESCRIPTION_MAX_LENGTH = 4000
_SUMMARY_MAX_LENGTH = 200
_STEPS_MAX_LENGTH = 8000
_SOURCE_MAX_LENGTH = 200

VehicleField = Annotated[
    str,
    Field(
        min_length=1,
        max_length=_VEHICLE_FIELD_MAX_LENGTH,
        pattern=_VEHICLE_FIELD_PATTERN,
    ),
]
Source = Annotated[str, Field(max_length=_SOURCE_MAX_LENGTH)]


def _safe_text_field(max_length: int) -> Any:
    return Field(max_length=max_length, pattern=_SAFE_TEXT_PATTERN)


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
    model_config = ConfigDict(str_strip_whitespace=True)

    brand: VehicleField
    model: VehicleField
    year: Annotated[int, Field(ge=1900, le=2030)]
    engine: VehicleField
    fuelType: FuelType
    doors: Annotated[int | None, Field(ge=0, le=10)] = None
    language: Locale = Locale.EN_GB


class TechSpecs(BaseModel):
    """Structured, alignment-checked technical specs - no free-form dict."""

    model_config = ConfigDict(extra="forbid")

    power_hp: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _rename_hp_alias(cls, data: Any) -> Any:
        """Rename a provider's stray "hp" key to the canonical "power_hp"."""
        if isinstance(data, dict) and "hp" in data:
            data = dict(data)
            hp_value = data.pop("hp")
            data.setdefault("power_hp", hp_value)
        return data


class AiFixResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = _safe_text_field(_SUMMARY_MAX_LENGTH)
    steps: str = _safe_text_field(_STEPS_MAX_LENGTH)
    estimatedCostEur: float | None = None


class AiKnownIssueResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = _safe_text_field(_TITLE_MAX_LENGTH)
    description: str = _safe_text_field(_DESCRIPTION_MAX_LENGTH)
    severity: IssueSeverity
    typicalKm: int | None = None
    sources: list[Source] | None = None
    fixes: list[AiFixResult]


class AiVehicleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str
    model: str
    name: str = Field(
        max_length=_NAME_MAX_LENGTH,
        description='Commercial name including generation when known, e.g. "Polo 6N1"',
    )
    year: int
    engine: str
    doors: int | None = None
    fuelType: FuelType | None = None
    techSpecs: TechSpecs | None = None


class LookupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle: AiVehicleResult
    knownIssues: list[AiKnownIssueResult]
