from app.schemas.lookup import LookupResponse
from app.schemas.translate import TranslateResponse


def lookup_response_json_schema() -> dict[str, object]:
    return LookupResponse.model_json_schema()


def translate_response_json_schema() -> dict[str, object]:
    return TranslateResponse.model_json_schema()
