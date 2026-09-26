from __future__ import annotations

import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile

from .ingestion.chunker import DocumentChunker
from .ingestion.docling_parser import DoclingParser
from .ingestion.repository import IngestionRepository
from .retrieval.embeddings import BGEEmbedder
from .retrieval.faiss_index import FaissChunkIndex
from .questions.generator import GroundedQuestionGenerator
from .config.settings import Settings
import psycopg

app = FastAPI(title="Generate Soal")
settings = Settings()
logger = logging.getLogger(__name__)
_allowed = {".pdf", ".docx", ".pptx"}
_embedder: BGEEmbedder | None = None
_index: FaissChunkIndex | None = None

def _authorized(api_key: str | None) -> None:
    if (settings.require_api_key or settings.api_key) and api_key != settings.api_key:
        raise HTTPException(401, "Invalid API key")


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with psycopg.connect(settings.postgres_dsn) as connection:
            connection.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}
    except Exception:
        raise HTTPException(503, "Database unavailable")


@app.post("/documents")
async def upload_document(file: UploadFile = File(...), x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    global _embedder, _index
    _authorized(x_api_key)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _allowed:
        raise HTTPException(400, "Expected PDF, DOCX, or PPTX")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "Uploaded file exceeds size limit")
    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        digest = hashlib.sha256(data).hexdigest()
        with psycopg.connect(settings.postgres_dsn) as connection:
            existing = IngestionRepository(connection).get_by_hash(digest)
        if existing:
            return {"document_id": existing.document_id, "file_hash": digest, "status": "duplicate"}
        document = DoclingParser().parse(path)
        chunks = DocumentChunker().chunk(document)
        with psycopg.connect(settings.postgres_dsn) as connection:
            repository = IngestionRepository(connection)
            repository.save(document, chunks)
            repository.set_status(document.document_id, "processing")
        _embedder = _embedder or BGEEmbedder(settings.embedding_model, settings.embedding_device, settings.embedding_dimensions)
        _index = _index or FaissChunkIndex(_embedder)
        _index.add([(chunk.chunk_id, chunk.text) for chunk in chunks])
        _index.save(Path(settings.faiss_index_path))
        with psycopg.connect(settings.postgres_dsn) as connection:
            IngestionRepository(connection).set_status(document.document_id, "completed")
    except Exception as exc:
        if "document" in locals():
            with psycopg.connect(settings.postgres_dsn) as connection:
                IngestionRepository(connection).set_status(document.document_id, "failed", str(exc))
        logger.exception("document ingestion failed")
        raise HTTPException(422, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)
    return {"document_id": document.document_id, "file_hash": digest, "status": "completed", "pages": len(document.pages), "chunks": len(chunks)}

@app.post("/search")
def search(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _authorized(x_api_key)
    query = str(payload.get("query", "")).strip()
    if not query:
        raise HTTPException(400, "query is required")
    global _embedder, _index
    _embedder = _embedder or BGEEmbedder(settings.embedding_model, settings.embedding_device, settings.embedding_dimensions)
    _index = _index or FaissChunkIndex.load(_embedder, Path(settings.faiss_index_path))
    if _index.index.ntotal == 0:
        return {"results": []}
    vector = _embedder.encode([query])
    limit = max(1, min(int(payload.get("limit", 5)), _index.index.ntotal))
    scores, rows = _index.index.search(vector, limit)
    pairs = [(int(row), float(score)) for row, score in zip(rows[0], scores[0]) if 0 <= row < len(_index.mapping)]
    ids = [_index.mapping[row] for row, _ in pairs]
    with psycopg.connect(settings.postgres_dsn) as connection:
        results = IngestionRepository(connection).search_chunks(ids)
    by_id = {item["chunk_id"]: item for item in results}
    return {"results": [{**by_id[chunk_id], "score": score} for row, score in pairs if (chunk_id := _index.mapping[row]) in by_id]}

@app.post("/questions")
def generate_questions(payload: dict[str, Any], x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    _authorized(x_api_key)
    sources = payload.get("sources", [])
    if not sources:
        raise HTTPException(400, "sources are required")
    try:
        questions = GroundedQuestionGenerator().generate(
            sources,
            count=int(payload.get("count", 3)),
            question_type=str(payload.get("type", "essay")),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"questions": questions}