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