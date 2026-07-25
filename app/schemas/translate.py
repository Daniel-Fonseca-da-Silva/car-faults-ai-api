from pydantic import BaseModel

from app.schemas.lookup import AiKnownIssueResult, Locale


class TranslateRequest(BaseModel):
    targetLanguage: Locale
    sourceLanguage: Locale
    knownIssues: list[AiKnownIssueResult]


class TranslateResponse(BaseModel):
    knownIssues: list[AiKnownIssueResult]
