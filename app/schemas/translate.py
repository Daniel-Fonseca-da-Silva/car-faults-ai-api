from pydantic import BaseModel, ConfigDict

from app.schemas.lookup import AiKnownIssueResult, Locale


class TranslateRequest(BaseModel):
    targetLanguage: Locale
    sourceLanguage: Locale
    knownIssues: list[AiKnownIssueResult]


class TranslateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knownIssues: list[AiKnownIssueResult]
