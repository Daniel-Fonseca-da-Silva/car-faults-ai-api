from app.prompts.loader import (
    build_translate_user_prompt,
    build_user_prompt,
    load_example,
    load_system_prompt,
    load_translate_example,
    load_translate_system_prompt,
)
from app.schemas.lookup import (
    AiKnownIssueResult,
    FuelType,
    IssueSeverity,
    Locale,
    LookupRequest,
)
from app.schemas.translate import TranslateRequest
from app.services.providers.util import extract_json_object


def test_load_system_prompt_mentions_json_shape():
    prompt = load_system_prompt()

    assert "JSON" in prompt
    assert "knownIssues" in prompt


def test_load_example_matches_polo_shape():
    example = load_example()

    assert example["vehicle"]["brand"] == "Volkswagen"
    assert example["vehicle"]["name"] == "Polo 6C"
    assert example["knownIssues"]


def test_build_user_prompt_includes_vehicle_fields():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
        doors=5,
    )

    prompt = build_user_prompt(request)

    assert "brand=Seat" in prompt
    assert "model=Ibiza" in prompt
    assert "fuelType=diesel" in prompt
    assert "doors=5" in prompt


def test_build_user_prompt_handles_missing_doors():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
    )

    prompt = build_user_prompt(request)

    assert "doors=unknown" in prompt


def test_build_user_prompt_defaults_language_to_en_gb():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
    )

    prompt = build_user_prompt(request)

    assert "language=en-GB" in prompt


def test_build_user_prompt_includes_requested_language():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
        language=Locale.PT_PT,
    )

    prompt = build_user_prompt(request)

    assert "language=pt-PT" in prompt


def test_load_translate_system_prompt_mentions_json_shape():
    prompt = load_translate_system_prompt()

    assert "JSON" in prompt
    assert "knownIssues" in prompt


def test_load_translate_example_matches_known_issues_shape():
    example = load_translate_example()

    assert example["knownIssues"]
    assert "title" in example["knownIssues"][0]


def test_build_translate_user_prompt_includes_languages_and_known_issues():
    request = TranslateRequest(
        sourceLanguage=Locale.EN_GB,
        targetLanguage=Locale.PT_PT,
        knownIssues=[
            AiKnownIssueResult(
                title="Gearbox",
                description="Wears out",
                severity=IssueSeverity.HIGH,
                fixes=[],
            )
        ],
    )

    prompt = build_translate_user_prompt(request)

    assert "sourceLanguage=en-GB" in prompt
    assert "targetLanguage=pt-PT" in prompt
    assert "Gearbox" in prompt


def test_extract_json_object_plain():
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_extract_json_object_strips_markdown_fence():
    text = '```json\n{"a": 1}\n```'

    assert extract_json_object(text) == {"a": 1}


def test_extract_json_object_strips_surrounding_text():
    text = 'Here you go:\n{"a": 1}\nThanks!'

    assert extract_json_object(text) == {"a": 1}
