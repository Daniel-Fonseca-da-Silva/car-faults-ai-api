import json
import logging
from pathlib import Path
from typing import Any

from app.schemas.lookup import LookupRequest
from app.services.retrieval.models import KnowledgeChunk

logger = logging.getLogger(__name__)

# Scoring weights - brand is a hard filter (see _score), the rest are
# additive bonuses so a closer match (same year range, same engine) ranks
# above a same brand/model entry that only partially fits.
_MODEL_MATCH_SCORE = 5
_YEAR_IN_RANGE_SCORE = 3
_ENGINE_MATCH_SCORE = 2


class KeywordRetriever:
    """Minimal keyword-based retrieval over `app/knowledge` (RAG Fase 1).

    No embeddings/vector store - scores the lightweight `index.json`
    entries against the request, then loads only the matched chunk files
    from `chunks/`.
    """

    def __init__(self, knowledge_dir: Path) -> None:
        self._index_path = knowledge_dir / "index.json"
        self._chunks_dir = knowledge_dir / "chunks"

    def retrieve(
        self, request: LookupRequest, *, max_chunks: int = 5
    ) -> list[KnowledgeChunk]:
        scored = [
            (score, entry)
            for entry in self._load_index()
            if (score := self._score(entry, request)) > 0
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        chunks = []
        for _, entry in scored[:max_chunks]:
            chunk = self._load_chunk(entry.get("id", ""))
            if chunk is not None:
                chunks.append(chunk)
        return chunks

    def _load_index(self) -> list[dict[str, Any]]:
        if not self._index_path.exists():
            return []
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("rag_index_load_failed path=%s", self._index_path)
            return []
        return data if isinstance(data, list) else []

    def _score(self, entry: dict[str, Any], request: LookupRequest) -> int:
        entry_brand = str(entry.get("brand", "")).strip().lower()
        if entry_brand != request.brand.strip().lower():
            return 0

        entry_model = str(entry.get("model", "")).strip().lower()
        model = request.model.strip().lower()
        model_matches = (
            entry_model == model or entry_model in model or model in entry_model
        )
        if not model_matches:
            return 0

        score = _MODEL_MATCH_SCORE

        year_from = entry.get("yearFrom")
        year_to = entry.get("yearTo")
        if (
            isinstance(year_from, int)
            and isinstance(year_to, int)
            and year_from <= request.year <= year_to
        ):
            score += _YEAR_IN_RANGE_SCORE

        entry_engine = str(entry.get("engine", "")).strip().lower()
        if entry_engine and entry_engine == request.engine.strip().lower():
            score += _ENGINE_MATCH_SCORE

        return score

    def _load_chunk(self, chunk_id: str) -> KnowledgeChunk | None:
        if not chunk_id:
            return None
        chunk_path = self._chunks_dir / f"{chunk_id}.json"
        try:
            data = json.loads(chunk_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("rag_chunk_load_failed id=%s path=%s", chunk_id, chunk_path)
            return None
        try:
            return KnowledgeChunk(**data)
        except (TypeError, ValueError):
            logger.warning("rag_chunk_invalid id=%s path=%s", chunk_id, chunk_path)
            return None
