from __future__ import annotations

from typing import Any

import numpy as np


class BGEEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu", dimensions: int = 1024, model: Any = None) -> None:
        self.dimensions = dimensions
        self._model = model
        if model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        vectors = self._model.encode(texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True)
        result = np.asarray(vectors, dtype="float32")
        if result.ndim != 2 or result.shape[1] != self.dimensions:
            raise ValueError(f"Expected embedding dimension {self.dimensions}, got {result.shape}")
        return result