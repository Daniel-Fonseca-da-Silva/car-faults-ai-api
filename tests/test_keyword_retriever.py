import json
from pathlib import Path

import pytest

from app.schemas.lookup import FuelType, LookupRequest
from app.services.retrieval.keyword_retriever import KeywordRetriever

REQUEST = LookupRequest(
    brand="Volkswagen",
    model="Polo",
    year=2015,
    engine="1.2 TSI",
    fuelType=FuelType.GASOLINE,
)


def _write_chunk(knowledge_dir: Path, **overrides: object) -> dict[str, object]:
    chunk = {
        "id": "vw-polo-ac",
        "brand": "Volkswagen",
        "model": "Polo",
        "yearFrom": 2014,
        "yearTo": 2017,
        "engine": "1.2 TSI",
        "issue": "Air conditioning compressor failure",
        "content": "Weak cooling common on the Polo 6C 1.2 TSI.",
        "severity": "medium",
        "typicalKm": 90000,
        "sourceUrl": "https://example.com/vw-polo-ac",
        **overrides,
    }
    chunks_dir = knowledge_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    (chunks_dir / f"{chunk['id']}.json").write_text(json.dumps(chunk), encoding="utf-8")
    return chunk


def _write_index(knowledge_dir: Path, entries: list[dict[str, object]]) -> None:
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "index.json").write_text(json.dumps(entries), encoding="utf-8")


def _index_entry(chunk: dict[str, object]) -> dict[str, object]:
    return {
        "id": chunk["id"],
        "brand": chunk["brand"],
        "model": chunk["model"],
        "yearFrom": chunk["yearFrom"],
        "yearTo": chunk["yearTo"],
        "engine": chunk.get("engine"),
    }


@pytest.fixture
def knowledge_dir(tmp_path: Path) -> Path:
    return tmp_path / "knowledge"


def test_retrieve_returns_matching_chunk_for_brand_and_model(knowledge_dir: Path):
    chunk = _write_chunk(knowledge_dir)
    _write_index(knowledge_dir, [_index_entry(chunk)])

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert [c.id for c in result] == ["vw-polo-ac"]
    assert result[0].content == chunk["content"]
    assert result[0].sourceUrl == chunk["sourceUrl"]


def test_retrieve_returns_empty_list_for_unknown_brand(knowledge_dir: Path):
    chunk = _write_chunk(knowledge_dir)
    _write_index(knowledge_dir, [_index_entry(chunk)])

    request = LookupRequest(
        brand="Toyota",
        model="Supra",
        year=2020,
        engine="3.0",
        fuelType=FuelType.GASOLINE,
    )
    result = KeywordRetriever(knowledge_dir).retrieve(request)

    assert result == []


def test_retrieve_returns_empty_list_when_no_index_file(knowledge_dir: Path):
    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert result == []


def test_retrieve_returns_empty_list_for_matching_brand_different_model(
    knowledge_dir: Path,
):
    chunk = _write_chunk(knowledge_dir)
    _write_index(knowledge_dir, [_index_entry(chunk)])

    request = LookupRequest(
        brand="Volkswagen",
        model="Golf",
        year=2015,
        engine="1.2 TSI",
        fuelType=FuelType.GASOLINE,
    )
    result = KeywordRetriever(knowledge_dir).retrieve(request)

    assert result == []


def test_retrieve_respects_max_chunks(knowledge_dir: Path):
    chunk_a = _write_chunk(knowledge_dir, id="vw-polo-ac")
    chunk_b = _write_chunk(knowledge_dir, id="vw-polo-dsg", issue="DSG wear")
    _write_index(knowledge_dir, [_index_entry(chunk_a), _index_entry(chunk_b)])

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST, max_chunks=1)

    assert len(result) == 1


def test_retrieve_scores_year_in_range_above_out_of_range(knowledge_dir: Path):
    in_range = _write_chunk(
        knowledge_dir, id="vw-polo-in-range", yearFrom=2014, yearTo=2017
    )
    out_of_range = _write_chunk(
        knowledge_dir, id="vw-polo-out-of-range", yearFrom=2000, yearTo=2005
    )
    _write_index(knowledge_dir, [_index_entry(out_of_range), _index_entry(in_range)])

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert [c.id for c in result] == ["vw-polo-in-range", "vw-polo-out-of-range"]


def test_retrieve_scores_engine_match_above_no_engine_match(knowledge_dir: Path):
    matching_engine = _write_chunk(
        knowledge_dir, id="vw-polo-tsi", engine="1.2 TSI", yearFrom=2000, yearTo=2030
    )
    other_engine = _write_chunk(
        knowledge_dir, id="vw-polo-tdi", engine="1.4 TDI", yearFrom=2000, yearTo=2030
    )
    _write_index(
        knowledge_dir, [_index_entry(other_engine), _index_entry(matching_engine)]
    )

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert [c.id for c in result] == ["vw-polo-tsi", "vw-polo-tdi"]


def test_retrieve_matches_brand_case_insensitively(knowledge_dir: Path):
    chunk = _write_chunk(knowledge_dir, brand="volkswagen")
    _write_index(knowledge_dir, [_index_entry(chunk)])

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert [c.id for c in result] == ["vw-polo-ac"]


def test_retrieve_skips_chunk_file_missing_on_disk(knowledge_dir: Path):
    chunk = _write_chunk(knowledge_dir)
    _write_index(
        knowledge_dir, [_index_entry(chunk), {**_index_entry(chunk), "id": "missing"}]
    )

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert [c.id for c in result] == ["vw-polo-ac"]


def test_retrieve_ignores_malformed_index_json(knowledge_dir: Path):
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "index.json").write_text("not valid json", encoding="utf-8")

    result = KeywordRetriever(knowledge_dir).retrieve(REQUEST)

    assert result == []
