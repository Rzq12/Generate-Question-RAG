from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import faiss

from .embeddings import BGEEmbedder


class FaissChunkIndex:
    def __init__(self, embedder: BGEEmbedder) -> None:
        self.embedder = embedder
        self.index = faiss.IndexFlatIP(embedder.dimensions)
        self.mapping: list[str] = []

    def add(self, chunks: Iterable[tuple[str, str]]) -> None:
        items = list(chunks)
        if not items:
            return
        vectors = self.embedder.encode([text for _, text in items])
        self.index.add(vectors)
        self.mapping.extend(chunk_id for chunk_id, _ in items)

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "chunks.faiss"))
        (directory / "chunks.jsonl").write_text("".join(json.dumps({"row": i, "chunk_id": value}) + "\n" for i, value in enumerate(self.mapping)), encoding="utf-8")