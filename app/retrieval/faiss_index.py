from __future__ import annotations

import json
import os
import tempfile
from threading import Lock
from pathlib import Path
from typing import Iterable

import faiss

from .embeddings import BGEEmbedder


class FaissChunkIndex:
    _lock = Lock()
    def __init__(self, embedder: BGEEmbedder) -> None:
        self.embedder = embedder
        self.index = faiss.IndexFlatIP(embedder.dimensions)
        self.mapping: list[str] = []

    @classmethod
    def load(cls, embedder: BGEEmbedder, directory: Path) -> "FaissChunkIndex":
        result = cls(embedder)
        index_path = directory / "chunks.faiss"
        mapping_path = directory / "chunks.jsonl"
        if index_path.exists() and mapping_path.exists():
            result.index = faiss.read_index(str(index_path))
            if result.index.d != embedder.dimensions:
                raise ValueError("FAISS index dimension does not match embedding model")
            result.mapping = [json.loads(line)["chunk_id"] for line in mapping_path.read_text(encoding="utf-8").splitlines() if line]
            if result.index.ntotal != len(result.mapping):
                raise ValueError("FAISS index and mapping are inconsistent")
        return result

    def add(self, chunks: Iterable[tuple[str, str]]) -> None:
        items = [(chunk_id, text) for chunk_id, text in chunks if chunk_id not in self.mapping]
        if not items:
            return
        vectors = self.embedder.encode([text for _, text in items])
        self.index.add(vectors)
        self.mapping.extend(chunk_id for chunk_id, _ in items)

    def save(self, directory: Path) -> None:
        with self._lock:
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=directory) as temp:
                temp_path = Path(temp)
                faiss.write_index(self.index, str(temp_path / "chunks.faiss"))
                (temp_path / "chunks.jsonl").write_text("".join(json.dumps({"row": i, "chunk_id": value}) + "\n" for i, value in enumerate(self.mapping)), encoding="utf-8")
                (temp_path / "metadata.json").write_text(json.dumps({"dimensions": self.embedder.dimensions, "model": self.embedder.model}), encoding="utf-8")
                for name in ("chunks.faiss", "chunks.jsonl", "metadata.json"):
                    os.replace(temp_path / name, directory / name)