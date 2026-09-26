from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .contracts import ParsedDocument


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    source_hash: str


class DocumentChunker:
    def __init__(self, max_chars: int = 1200) -> None:
        self.max_chars = max_chars

    def chunk(self, document: ParsedDocument) -> tuple[Chunk, ...]:
        if document.docling_document is not None:
            return self._chunk_docling(document)
        chunks: list[Chunk] = []
        for page in document.pages:
            text = page.text.strip()
            for offset in range(0, len(text), self.max_chars):
                value = text[offset : offset + self.max_chars].strip()
                if not value:
                    continue
                chunk_id = hashlib.sha256(f"{document.document_id}:{page.page_number}:{offset}:{value}".encode()).hexdigest()
                chunks.append(Chunk(chunk_id, document.document_id, page.page_number, value, page.source_hash))
        return tuple(chunks)

    def _chunk_docling(self, document: ParsedDocument) -> tuple[Chunk, ...]:
        try:
            from docling.chunking import HybridChunker
            raw_chunks = HybridChunker().chunk(document.docling_document)
        except Exception:
            return self._chunk_markdown(document)
        chunks: list[Chunk] = []
        for index, raw_chunk in enumerate(raw_chunks):
            text = str(getattr(raw_chunk, "text", raw_chunk)).strip()
            if not text:
                continue
            page_number = self._page_number(raw_chunk)
            source_hash = document.pages[page_number - 1].source_hash if 0 < page_number <= len(document.pages) else document.file_hash
            chunk_id = hashlib.sha256(f"{document.document_id}:{index}:{text}".encode()).hexdigest()
            chunks.append(Chunk(chunk_id, document.document_id, page_number, text, source_hash))
        return tuple(chunks)

    def _chunk_markdown(self, document: ParsedDocument) -> tuple[Chunk, ...]:
        chunks: list[Chunk] = []
        for page in document.pages:
            text = page.text.strip()
            for offset in range(0, len(text), self.max_chars):
                value = text[offset : offset + self.max_chars].strip()
                if value:
                    chunk_id = hashlib.sha256(f"{document.document_id}:{page.page_number}:{offset}:{value}".encode()).hexdigest()
                    chunks.append(Chunk(chunk_id, document.document_id, page.page_number, value, page.source_hash))
        return tuple(chunks)

    @staticmethod
    def _page_number(chunk: object) -> int:
        for item in getattr(chunk, "meta", None).doc_items if getattr(chunk, "meta", None) else ():
            for provenance in getattr(item, "prov", ()):
                page = getattr(provenance, "page_no", None)
                if page:
                    return int(page)
        return 1