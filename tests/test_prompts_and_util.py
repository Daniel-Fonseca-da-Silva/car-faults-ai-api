import json
import re

from app.prompts.loader import (
    build_translate_user_prompt,
    build_user_prompt,
    load_electric_example,
    load_example,
    load_heavy_vehicle_example,
    load_motorcycle_example,
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
from app.services.retrieval.models import KnowledgeChunk


def test_load_system_prompt_mentions_json_shape():
    prompt = load_system_prompt()

    assert "JSON" in prompt
    assert "knownIssues" in prompt


def test_load_system_prompt_mentions_vehicles_and_motorcycles():
    prompt = load_system_prompt()

    assert "vehicle" in prompt.lower()
    assert "motorcycle" in prompt.lower()


def test_load_system_prompt_covers_categories_beyond_car_and_motorcycle():
    prompt = load_system_prompt().lower()

    assert "truck" in prompt
    assert "boat" in prompt
    assert "aircraft" in prompt


def test_load_system_prompt_has_honesty_rule_for_obscure_vehicles():
    prompt = load_system_prompt().lower()

    assert "honesty" in prompt
    assert "obscure" in prompt


def test_load_system_prompt_has_domain_scope_and_security_sections():
    prompt = load_system_prompt()

    assert "Domain scope" in prompt
    assert "Prompt security" in prompt
    assert "brand" in prompt
    assert "engine" in prompt
    assert "fuelType" in prompt


def test_load_system_prompt_covers_injection_and_secret_threats():
    prompt = load_system_prompt().lower()

    assert "sql" in prompt
    assert "select" in prompt
    assert "jailbreak" in prompt
    assert "api key" in prompt
    assert "<<<vehicle_data>>>" in prompt


def test_load_example_matches_polo_shape():
    example = load_example()

    assert example["vehicle"]["brand"] == "Volkswagen"
    assert example["vehicle"]["name"] == "Polo 6C"
    assert example["knownIssues"]


def test_load_example_first_issue_uses_a_real_source_url():
    example = load_example()

    sources = example["knownIssues"][0]["sources"]

    assert sources
    assert sources[0].startswith("https://")


def test_load_example_second_issue_has_no_sources():
    example = load_example()

    assert "sources" not in example["knownIssues"][1]


def test_load_example_steps_follow_fixed_procedure_format():
    example = load_example()

    steps = example["knownIssues"][0]["fixes"][0]["steps"]

    assert "1)" in steps
    assert "2)" in steps
    assert "3)" in steps
    assert "4)" in steps


def test_load_motorcycle_example_matches_intruder_shape():
    example = load_motorcycle_example()

    assert example["vehicle"]["brand"] == "Suzuki"
    assert example["vehicle"]["model"] == "Intruder"
    assert "doors" not in example["vehicle"]
    assert example["knownIssues"]


def test_load_electric_example_has_no_combustion_issues():
    example = load_electric_example()

    assert example["vehicle"]["fuelType"] == "electric"
    assert example["vehicle"]["engine"] == "electric"
    assert example["knownIssues"]
    combined_text = json.dumps(example).lower()
    assert "dpf" not in combined_text
    assert re.search(r"\begr\b", combined_text) is None
    assert "timing chain" not in combined_text


def test_load_heavy_vehicle_example_omits_doors():
    example = load_heavy_vehicle_example()

    assert "doors" not in example["vehicle"]
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


def test_build_user_prompt_includes_car_and_motorcycle_examples():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
        doors=5,
    )

    prompt = build_user_prompt(request)

    assert "Polo 6C" in prompt
    assert "Intruder 125 (VL125)" in prompt


def test_build_user_prompt_selects_electric_example_for_electric_fuel_type():
    request = LookupRequest(
        brand="Nissan",
        model="Leaf",
        year=2019,
        engine="electric",
        fuelType=FuelType.ELECTRIC,
    )

    prompt = build_user_prompt(request)

    assert "Polo 6C" in prompt
    assert "Leaf ZE1" in prompt
    assert "Intruder 125 (VL125)" not in prompt


def test_build_user_prompt_selects_heavy_vehicle_example_for_truck_brand():
    request = LookupRequest(
        brand="Scania",
        model="R-series",
        year=2016,
        engine="DC13",
        fuelType=FuelType.DIESEL,
    )

    prompt = build_user_prompt(request)

    assert "Polo 6C" in prompt
    assert "Scania R-series (P/R generation)" in prompt
    assert "Intruder 125 (VL125)" not in prompt


def test_build_user_prompt_selects_motorcycle_example_for_motorcycle_only_brand():
    request = LookupRequest(
        brand="Ducati",
        model="Monster",
        year=2020,
        engine="937",
        fuelType=FuelType.GASOLINE,
    )

    prompt = build_user_prompt(request)

    assert "Polo 6C" in prompt
    assert "Intruder 125 (VL125)" in prompt


def test_build_user_prompt_injects_only_two_examples():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
        doors=5,
    )

    prompt = build_user_prompt(request)

    assert prompt.count('"vehicle"') == 2


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


def test_load_system_prompt_mentions_retrieved_context():
    prompt = load_system_prompt()

    assert "<<<RETRIEVED_CONTEXT>>>" in prompt
    assert "<<<END_RETRIEVED_CONTEXT>>>" in prompt


# --- RAG (RETRIEVED_CONTEXT injection) ---------------------------------------

_CHUNK = KnowledgeChunk(
    id="vw-polo-6c-ac",
    brand="Volkswagen",
    model="Polo",
    yearFrom=2014,
    yearTo=2017,
    engine="1.2 TSI",
    issue="Air conditioning compressor failure",
    content="Weak cooling common on the Polo 6C 1.2 TSI from 90,000 km.",
    sourceUrl="https://example.com/vw-polo-ac",
    severity="medium",
    typicalKm=90000,
)


def test_build_user_prompt_without_chunks_omits_retrieved_context():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
        doors=5,
    )

    prompt = build_user_prompt(request)

    assert "<<<RETRIEVED_CONTEXT>>>" not in prompt


def test_build_user_prompt_with_chunks_includes_retrieved_context():
    request = LookupRequest(
        brand="Volkswagen",
        model="Polo",
        year=2015,
        engine="1.2 TSI",
        fuelType=FuelType.GASOLINE,
        doors=5,
    )

    prompt = build_user_prompt(request, retrieved_chunks=[_CHUNK])

    assert "<<<RETRIEVED_CONTEXT>>>" in prompt
    assert "<<<END_RETRIEVED_CONTEXT>>>" in prompt
    assert "Air conditioning compressor failure" in prompt
    assert "https://example.com/vw-polo-ac" in prompt


def test_build_user_prompt_places_retrieved_context_between_vehicle_data_and_examples():
    request = LookupRequest(
        brand="Volkswagen",
        model="Polo",
        year=2015,
        engine="1.2 TSI",
        fuelType=FuelType.GASOLINE,
        doors=5,
    )

    prompt = build_user_prompt(request, retrieved_chunks=[_CHUNK])

    vehicle_end = prompt.index("<<<END_VEHICLE_DATA>>>")
    context_start = prompt.index("<<<RETRIEVED_CONTEXT>>>")
    context_end = prompt.index("<<<END_RETRIEVED_CONTEXT>>>")
    examples_marker = prompt.index("Below are two examples")

    assert vehicle_end < context_start < context_end < examples_marker


def test_load_translate_system_prompt_mentions_json_shape():
    prompt = load_translate_system_prompt()

    assert "JSON" in prompt
    assert "knownIssues" in prompt


def test_load_translate_system_prompt_covers_injection_and_secret_threats():
    prompt = load_translate_system_prompt().lower()

    assert "ignore" in prompt
    assert "system prompt" in prompt
    assert "sql" in prompt


def test_load_translate_example_matches_known_issues_shape():
    example = load_translate_example()

    assert example["knownIssues"]
    assert "title" in example["knownIssues"][0]


def test_load_translate_example_first_issue_uses_same_real_source_url():
    example = load_example()
    translated = load_translate_example()

    translated_sources = translated["knownIssues"][0]["sources"]
    example_sources = example["knownIssues"][0]["sources"]

    assert translated_sources == example_sources


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


def test_build_user_prompt_wraps_vehicle_data_in_delimiters():
    request = LookupRequest(
        brand="Seat",
        model="Ibiza",
        year=2019,
        engine="1.0 TSI",
        fuelType=FuelType.DIESEL,
    )

    prompt = build_user_prompt(request)

    assert "<<<VEHICLE_DATA>>>" in prompt
    assert "<<<END_VEHICLE_DATA>>>" in prompt
    assert prompt.index("<<<VEHICLE_DATA>>>") < prompt.index("brand=Seat")
    assert prompt.index("brand=Seat") < prompt.index("<<<END_VEHICLE_DATA>>>")


def test_build_translate_user_prompt_wraps_known_issues_in_delimiters():
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

    assert "<<<VEHICLE_DATA>>>" in prompt
    assert "<<<END_VEHICLE_DATA>>>" in prompt
    assert prompt.index("<<<VEHICLE_DATA>>>") < prompt.index("Gearbox")
    assert prompt.index("Gearbox") < prompt.index("<<<END_VEHICLE_DATA>>>")


def test_extract_json_object_plain():
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_extract_json_object_strips_markdown_fence():
    text = '```json\n{"a": 1}\n```'

    assert extract_json_object(text) == {"a": 1}


def test_extract_json_object_strips_surrounding_text():
    text = 'Here you go:\n{"a": 1}\nThanks!'

    assert extract_json_object(text) == {"a": 1}
