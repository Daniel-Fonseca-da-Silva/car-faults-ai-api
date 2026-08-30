from pydantic import BaseModel, ConfigDict


class KnowledgeChunk(BaseModel):
    """A single curated knowledge-base entry used to ground `/lookup` output.

    Loaded from `app/knowledge/chunks/<id>.json` - see
    `app/knowledge/index.json` for the lightweight metadata used to select
    which chunk files to load.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    brand: str
    model: str
    yearFrom: int
    yearTo: int
    issue: str
    content: str
    engine: str | None = None
    sourceUrl: str | None = None
    severity: str | None = None
    typicalKm: int | None = None
