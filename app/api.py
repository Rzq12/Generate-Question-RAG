from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile

from .ingestion.chunker import DocumentChunker
from .ingestion.docling_parser import DoclingParser

app = FastAPI(title="Generate Soal")
_allowed = {".pdf", ".docx", ".pptx"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _allowed:
        raise HTTPException(400, "Expected PDF, DOCX, or PPTX")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        document = DoclingParser().parse(path)
        chunks = DocumentChunker().chunk(document)
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)
    return {"document_id": document.document_id, "file_hash": hashlib.sha256(data).hexdigest(), "pages": len(document.pages), "chunks": len(chunks)}