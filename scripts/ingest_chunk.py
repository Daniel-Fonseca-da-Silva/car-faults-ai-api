#!/usr/bin/env python3
"""Add or update a single RAG knowledge chunk (app/knowledge/, Fase 1).

Writes the chunk to app/knowledge/chunks/<id>.json and upserts its metadata
in app/knowledge/index.json. Run from the repository root:

    python scripts/ingest_chunk.py \\
        --id vw-polo-6c-ac \\
        --brand Volkswagen --model Polo \\
        --year-from 2014 --year-to 2017 \\
        --engine "1.2 TSI" \\
        --issue "Air conditioning compressor and refrigerant leak" \\
        --content "Weak or absent cooling is usually a slow refrigerant leak..." \\
        --severity medium --typical-km 90000 \\
        --source-url "https://www.auto-doc.pt/info/volkswagen-polo-problemas-associados"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.retrieval.models import KnowledgeChunk  # noqa: E402

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "app" / "knowledge"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--id", required=True, help="Unique chunk id, e.g. vw-polo-6c-ac"
    )
    parser.add_argument("--brand", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--year-from", type=int, required=True)
    parser.add_argument("--year-to", type=int, required=True)
    parser.add_argument("--issue", required=True, help="Short issue title")
    parser.add_argument("--content", required=True, help="Full chunk write-up")
    parser.add_argument("--engine", default=None)
    parser.add_argument("--source-url", default=None)
    parser.add_argument(
        "--severity", default=None, choices=["low", "medium", "high", "critical"]
    )
    parser.add_argument("--typical-km", type=int, default=None)
    return parser.parse_args()


def _write_chunk(chunk: KnowledgeChunk) -> Path:
    chunks_dir = _KNOWLEDGE_DIR / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    path = chunks_dir / f"{chunk.id}.json"
    payload = chunk.model_dump(exclude_none=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _upsert_index_entry(chunk: KnowledgeChunk) -> Path:
    index_path = _KNOWLEDGE_DIR / "index.json"
    entries = []
    if index_path.exists():
        entries = json.loads(index_path.read_text(encoding="utf-8"))

    entry = {
        "id": chunk.id,
        "brand": chunk.brand,
        "model": chunk.model,
        "yearFrom": chunk.yearFrom,
        "yearTo": chunk.yearTo,
        "engine": chunk.engine,
        "tags": [chunk.issue],
    }
    if chunk.sourceUrl:
        entry["sourceUrl"] = chunk.sourceUrl
    entry = {key: value for key, value in entry.items() if value is not None}

    entries = [existing for existing in entries if existing.get("id") != chunk.id]
    entries.append(entry)
    entries.sort(
        key=lambda existing: (existing["brand"], existing["model"], existing["id"])
    )

    index_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return index_path


def main() -> None:
    args = _parse_args()

    chunk = KnowledgeChunk(
        id=args.id,
        brand=args.brand,
        model=args.model,
        yearFrom=args.year_from,
        yearTo=args.year_to,
        engine=args.engine,
        issue=args.issue,
        content=args.content,
        sourceUrl=args.source_url,
        severity=args.severity,
        typicalKm=args.typical_km,
    )

    chunk_path = _write_chunk(chunk)
    index_path = _upsert_index_entry(chunk)
    print(f"Wrote {chunk_path}")
    print(f"Updated {index_path}")


if __name__ == "__main__":
    main()
